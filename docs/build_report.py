"""Build the project report from a copy of the current database."""
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as PDFImage

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'docs' / 'report_assets'
ASSETS.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('Arial', '/System/Library/Fonts/Supplemental/Arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialBold', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
styles = getSampleStyleSheet()
for name in ('Normal', 'BodyText'):
    styles[name].fontName = 'Arial'
    styles[name].fontSize = 10
    styles[name].leading = 15
styles.add(ParagraphStyle(name='TitleRu', fontName='ArialBold', fontSize=24, leading=30, spaceAfter=18))
styles.add(ParagraphStyle(name='HeadingRu', fontName='ArialBold', fontSize=15, leading=20, spaceAfter=12))
styles.add(ParagraphStyle(name='SubRu', fontName='ArialBold', fontSize=11, leading=16, spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle(name='CaptionRu', fontName='Arial', fontSize=8, leading=11, textColor=colors.HexColor('#526078'), spaceAfter=12))
story = []

def p(text, style='BodyText'):
    story.append(Paragraph(text, styles[style]))
    story.append(Spacer(1, 7))

def table(rows, widths):
    cells = [[Paragraph(escape(str(v)), styles['BodyText']) for v in row] for row in rows]
    obj = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
    obj.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eef6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#ccd5e1')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(obj)
    story.append(Spacer(1, 12))

def screen(name, transcript):
    # Render actual captured console output; do not invent program responses.
    lines = transcript.strip().splitlines()
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 19)
    width = max(900, int(max(font.getlength(line) for line in lines)) + 48)
    img = Image.new('RGB', (width, 62 + 27 * len(lines)), '#101827')
    draw = ImageDraw.Draw(img)
    draw.text((22, 12), 'AIRLINES / Python console output', font=font, fill='#7dd3fc')
    for i, line in enumerate(lines):
        draw.text((22, 48 + 27 * i), line, font=font, fill='#e5e7eb')
    path = ASSETS / f'{name}.png'
    img.save(path)
    (ASSETS / f'{name}.txt').write_text(transcript, encoding='utf-8')
    return path, img.size

def picture(data, max_height=250):
    path, (w, h) = data
    scale = min(499 / w, max_height / h)
    story.append(PDFImage(str(path), width=w * scale, height=h * scale, hAlign='LEFT'))
    story.append(Spacer(1, 7))

with tempfile.TemporaryDirectory(prefix='airlines-report-') as folder:
    db = Path(folder) / 'report-demo.db'
    source = sqlite3.connect(f'file:{ROOT / "project.db"}?mode=ro', uri=True)
    target = sqlite3.connect(db)
    source.backup(target)
    target.close()
    source.close()
    conn = sqlite3.connect(db)
    flights, seats = conn.execute('SELECT COUNT(*), SUM(seats) FROM flights').fetchone()
    passengers = conn.execute('SELECT COUNT(*) FROM passengers').fetchone()[0]
    tickets, revenue = conn.execute('SELECT COUNT(*), SUM(price) FROM tickets').fetchone()
    name = conn.execute('SELECT name FROM passengers ORDER BY id LIMIT 1').fetchone()[0]
    conn.close()

    def run(lines):
        result = subprocess.run([sys.executable, str(ROOT / 'main.py'), '--database', str(db)],
            input='\n'.join(lines) + '\n', text=True, capture_output=True, check=True)
        return result.stdout

    summary = run(['6', '0'])
    stats_start = summary.index('AIRLINE RESERVATION SYSTEM', summary.index('Choose an option:'))
    stats_end = summary.index('\nAIRLINE RESERVATION SYSTEM', stats_start)
    summary_image = screen('statistics', summary[stats_start:stats_end])
    search = run(['3', '1', name, '0'])
    start = search.index('1. Passenger by name or ID')
    end = search.index('\nAIRLINE RESERVATION SYSTEM', start)
    search_image = screen('search', search[start:end])
    demonstration = run(['1', '2', 'Report Demo Student', 'report-demo@example.com', '0'])
    start = demonstration.index('1. Flight')
    end = demonstration.index('\nAIRLINE RESERVATION SYSTEM', start)
    add_image = screen('add_passenger', demonstration[start:end])
    export = run(['7', '0'])
    report_text = db.with_suffix('.results.txt').read_text(encoding='utf-8')
    assert 'Report Demo Student' in report_text
    (ASSETS / 'demo_export.txt').write_text(report_text, encoding='utf-8')

team_path = ASSETS / 'team.json'
team = json.loads(team_path.read_text()) if team_path.exists() else None
occupancy = tickets / seats * 100 if seats else 0
money = f'{revenue:,}'.replace(',', ' ')

p('Airline Reservation System', 'TitleRu')
p('Midterm Project Report: Python Management System', 'HeadingRu')
p(f'A console-based airline reservation system built with Python and SQLite.')
p('Project Team', 'SubRu')
if team:
    if team.get('group'):
        p('Group: ' + escape(team['group']))
    table([['Team Member', 'Contribution']] + [[x['name'], x['contribution']] for x in team['members']], [160, 339])
else:
    p('<b>Draft:</b> team details and contributions are awaiting confirmation.')
    table([['Team Member', 'Contribution'], ['[Team member 1]', '[Enter actual contribution]'], ['[Team member 2]', '[Enter actual contribution]'], ['[Team member 3]', '[Enter actual contribution]']], [180, 319])
p('Project Objective', 'SubRu')
p('The project provides a console application for managing flights, passengers and tickets. Users can add, view, search, update and delete records, book seats, cancel tickets and export results.')
p('The application models reservation management. It does not process payments, connect to airline services or track refund history. Prices are stored as whole amounts in Kazakhstani tenge.')
p('Technologies and Startup', 'SubRu')
p('The application requires Python and uses standard library modules: sqlite3, re, random, datetime, pathlib and argparse. No third-party packages are required to run the application. Start it with <b>python3 main.py</b>. The project.db database persists between runs.')
story.append(PageBreak())

p('Database Structure', 'HeadingRu')
p('SQLite stores data in three related tables. Each table has an id primary key. In tickets, flight_id and passenger_id are foreign keys.')
table([['Table', 'Fields and Purpose'], ['flights', 'id, number, origin, destination, departure, seats, price. Stores the flight number, route, departure time, seat capacity and current price.'], ['passengers', 'id, name, email. Stores passenger details; email is unique.'], ['tickets', 'id, flight_id, passenger_id, seat, price. Stores the flight, passenger, seat number and price at booking.']], [95, 404])
p('Table Relationships', 'SubRu')
table([['Relationship', 'Cardinality'], ['flights.id → tickets.flight_id', 'One flight to many tickets'], ['passengers.id → tickets.passenger_id', 'One passenger to many tickets'], ['passengers ↔ flights through tickets', 'Many to many']], [280, 219])
p('Integrity Constraints', 'SubRu')
p('PRAGMA foreign_keys = ON enables relationship checks. A ticket cannot reference a nonexistent passenger or flight. UNIQUE(flight_id, seat) prevents double booking of a seat, while UNIQUE(flight_id, passenger_id) prevents a passenger from holding two tickets for the same flight. Related tickets must be cancelled before deleting a flight or passenger.')
p('Data Sources', 'SubRu')
p('The dataset is synthetic and is generated by seed() or entered through the menu. The generator creates 20 flights, 50 passengers and 40 tickets only when all three tables are empty. random.Random(26) makes generation reproducible. Initial flights depart from Almaty; other origins can be entered manually. No external API is used.')
p(f'After manual changes, the current database contains {flights} flights, {passengers} passengers and {tickets} tickets. This meets the minimum dataset requirement of 20 / 50 / 40.')
story.append(PageBreak())

p('Main Functions and Classes', 'HeadingRu')
table([['Module', 'Responsibility'], ['main.py', 'Console interface: input, menus, table display and error handling.'], ['database.py / Database', 'SQLite connection, table creation, SQL execution and initial data generation.'], ['airline.py / AirlineSystem', 'Booking rules, validation, search, CRUD operations, statistics and export.']], [165, 334])
p('Input and Menus', 'SubRu')
p('read_text() repeats the prompt for empty input. read_number() accepts positive integers. choose_record() selects a record type. display_records() calculates column widths and prints a table. The main() loop continues until the user selects option 0.')
p('Booking and Updates', 'SubRu')
p('add_ticket() calls check_booking() to verify the flight and passenger, the seat range, seat availability and duplicate bookings. The flight price is copied to the ticket. Updating a flight price does not change existing ticket prices; moving a ticket to another flight uses the new flight price. update_flight() prevents reducing capacity below the highest booked seat number.')
p('Search and File Handling', 'SubRu')
p('search_passengers() searches by exact ID or part of a name; search_flights() searches by part of a destination name. The registered SQL function casefold supports case-insensitive searches, including Cyrillic text. If no matches are found, the program displays No records found. export_results() writes records and statistics to a text file.')
p('Two Additional Features', 'SubRu')
p('<b>re:</b> regular expressions validate flight numbers, date format and email addresses. datetime.strptime() also checks calendar validity.<br/><b>random:</b> generates flight capacities and prices and selects 40 distinct passengers for initial tickets.')
p('Example operation flow: main.py → add_ticket() → check_booking() → Database.execute() → INSERT INTO tickets → transaction commit.')
story.append(PageBreak())

p('Program Demonstration', 'HeadingRu')
p('The figures below render actual console output captured from main.py running on a temporary copy of project.db. They are images of captured output rather than screenshots of a terminal window. The original database was unchanged.', 'CaptionRu')
picture(search_image, 180)
p('Figure 1. Searching for a passenger by name and displaying matching records.', 'CaptionRu')
picture(add_image, 190)
p('Figure 2. Successfully adding a demonstration passenger to the database copy. Input was supplied automatically, so user responses are not echoed in the captured output.', 'CaptionRu')
p('Persistence and Export Check', 'SubRu')
p('After adding the demonstration passenger, the application was restarted using the same temporary database and option 7 was used to export results. The exported report contains Report Demo Student, confirming persistence between runs. This demonstration record is excluded from the original database calculations on the next page.')
p('The defense demonstration should also cover ticket creation, rejection of an occupied seat, record updates and booking cancellation. Each team member should understand how user input leads to validation and SQL queries.')
story.append(PageBreak())

p('Calculations and Results', 'HeadingRu')
picture(summary_image, 185)
p('Figure 3. Statistics from the project database before demonstration changes.', 'CaptionRu')
table([['Metric', 'Value'], ['Flights / passengers / tickets', f'{flights} / {passengers} / {tickets}'], ['Total seat capacity', str(seats)], ['Active ticket revenue', f'{money} KZT'], ['Overall seat occupancy', f'{occupancy:.2f}%']], [300, 199])
p('Formulas', 'SubRu')
p(f'<b>Revenue</b> = SUM(tickets.price) = {money} KZT. Only stored active tickets are counted; cancellation deletes a ticket and reduces the total.<br/><b>Occupancy</b> = ticket count / total seat capacity × 100 = {tickets} / {seats} × 100 = {occupancy:.2f}%. If total capacity is zero, occupancy is 0.')
p('Exported Report Contents', 'SubRu')
p('results.txt contains summary metrics, flights with individual occupancy rates, passengers and tickets. Statistics include all stored flights. Past departure dates are allowed; time zones are not calculated.')

def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#ccd5e1'))
    canvas.line(48, 43, 547, 43)
    canvas.setFont('Arial', 8)
    canvas.setFillColor(colors.HexColor('#526078'))
    canvas.drawRightString(547, 30, str(doc.page))

output = ROOT / 'ProjectReport.pdf'
SimpleDocTemplate(str(output), pagesize=(595.28, 841.89), rightMargin=48, leftMargin=48,
    topMargin=45, bottomMargin=58, title='Airline Reservation System — Project Report',
    author='Airline Reservation System project team').build(story, onFirstPage=footer, onLaterPages=footer)
print(output)
