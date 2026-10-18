"""Slide content executed by build_presentation.py after its drawing helpers."""
import io
import keyword
import tokenize
from PIL import ImageDraw, ImageFont

ASSETS=ROOT/'docs/report_assets/code'
ASSETS.mkdir(exist_ok=True)
CODE_SCREENSHOTS = {
    ('database.py', 40, 51): ('18.25.03', .63, 1.0),
    ('database.py', 61, 65): ('18.25.22', 0, .26),
    ('airline.py', 62, 70): ('18.25.34', 0, 1.0),
    ('airline.py', 55, 60): ('18.25.54', 0, 1.0),
    ('airline.py', 78, 93): ('18.26.06', 0, 1.0),
    ('airline.py', 102, 108): ('18.26.14', 0, 1.0),
    ('airline.py', 130, 137): ('18.26.22', 0, 1.0),
}

def image_file(path,x,y,w,h):
    im=Image.open(path)
    iw,ih=im.size
    scale=min(w/iw,h/ih)
    dw,dh=iw*scale,ih*scale
    x+=(w-dw)/2
    slide.shapes.add_picture(str(path),Pt(x),Pt(y),width=Pt(dw),height=Pt(dh))
    pdf.drawImage(str(path),x,H-y-dh,width=dw,height=dh)

def source_image(file,start,end):
    capture, top, bottom = CODE_SCREENSHOTS[(file, start, end)]
    original = ROOT/'docs/screenshots/code'/f'Screenshot 2026-10-18 at {capture}.png'
    if top == 0 and bottom == 1:
        return original
    im = Image.open(original)
    im = im.crop((0, round(im.height * top), im.width, round(im.height * bottom)))
    path = ASSETS/f'vscode_{Path(file).stem}_{start}_{end}.png'
    im.save(path)
    return path

def rendered_source_image(file,start,end):
    source=(ROOT/file).read_text()
    all_lines=source.splitlines()
    lines=all_lines[start-1:end]
    font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',26)
    small=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',21)
    cw=font.getlength('M')
    width=max(1050,int(max(len(s) for s in lines)*cw)+120)
    im=Image.new('RGB',(width,82+len(lines)*36),'#1e1e1e')
    draw=ImageDraw.Draw(im)
    draw.text((24,15),f'{file}  |  lines {start}-{end}  |  source code',font=small,fill='#9cdcfe')
    for i,line in enumerate(lines):
        draw.text((14,65+i*36),str(start+i).rjust(3),font=small,fill='#858585')
        draw.text((88,60+i*36),line,font=font,fill='#d4d4d4')
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        color=None
        if token.type==tokenize.STRING: color='#ce9178'
        elif token.type==tokenize.COMMENT: color='#6a9955'
        elif token.type==tokenize.NUMBER: color='#b5cea8'
        elif token.type==tokenize.NAME:
            color='#c586c0' if keyword.iskeyword(token.string) else '#9cdcfe'
        if color:
            for lineno in range(max(start,token.start[0]),min(end,token.end[0])+1):
                a=token.start[1] if lineno==token.start[0] else 0
                b=token.end[1] if lineno==token.end[0] else len(all_lines[lineno-1])
                segment=all_lines[lineno-1][a:b]
                draw.text((88+cw*a,60+(lineno-start)*36),segment,font=font,fill=color)
    path=ASSETS/f'{Path(file).stem}_{start}_{end}.png'
    im.save(path)
    return path

def code_slide(title,file,start,end,explanation,presenter):
    new(title,f'{file} • VS Code screenshot',presenter,explanation)
    image_file(source_image(file,start,end),42,145,876,275)
    for i,line in enumerate(textwrap.wrap(explanation,width=91)):
        text(42,435+i*23,876,line,17,MUTED)

def terminal(title,time,result,explanation,presenter='Kushekbayev Batyrlan',crop=False):
    new(title,result,presenter,explanation)
    path=ROOT/'docs/screenshots'/f'Screenshot 2026-10-18 at {time}.png'
    if crop:
        im=Image.open(path)
        im=im.crop((0,im.height-285,im.width,im.height))
        path=ASSETS/'booking_terminal.png'
        im.save(path)
    image_file(path,42,145,876,275)
    for i,line in enumerate(textwrap.wrap(explanation,width=91)):
        text(42,435+i*23,876,line,17,MUTED)

new('Airline Reservation System','A practical walkthrough: user input → stored data → results.',
    'All team members','We will demonstrate the app in the terminal and explain the exact source code behind its actions.')
text(42,175,876,'Python console application + SQLite database',28,TEAL,bold=True)
text(42,235,876,'Manage flights, passengers and tickets.',24)
text(42,285,876,'Book seats, search records, update details and cancel tickets.',21)
text(42,335,876,'Calculate revenue and occupancy. Export results.txt.',21)

new('Three modules, one workflow','The menu collects input; booking rules validate it; SQLite stores it.',
    'All team members','main.py handles input and output. AirlineSystem handles application rules. Database handles storage.')
for x,title,desc in [(42,'main.py','Batyrlan\nInput and output\nMenus and errors'),(346,'airline.py','Alibek\nBooking and search\nStatistics and export'),(650,'database.py','Batyr\nTables and SQL\nPersistent data')]:
    rect(x,175,268,190)
    text(x+18,190,232,title,23,TEAL,bold=True)
    text(x+18,241,232,desc,20)
text(314,245,29,'→',22,ORANGE)
text(618,245,29,'→',22,ORANGE)
text(42,421,876,'Example: enter a seat → check availability → save a ticket → show its ID.',18,MUTED)

new('How the tables are connected','A ticket links one passenger to one flight.',
    'Aben Batyr','Flights and passengers each have many tickets. Tickets implement the many-to-many relationship between them.')
for x,title,desc in [(42,'flights','id [primary key]\nroute and departure\ncapacity and price'),(346,'tickets','flight_id [foreign key]\npassenger_id [foreign key]\nseat and booking price'),(650,'passengers','id [primary key]\nname\nunique email')]:
    rect(x,175,268,190)
    text(x+16,190,236,title,25,TEAL,bold=True)
    text(x+16,245,236,desc,16)
text(314,238,29,'1:N',11,ORANGE)
text(618,238,29,'N:1',11,ORANGE)
text(42,416,876,'One flight → many tickets. One passenger → tickets on different flights.',18,MUTED)

code_slide('Database: protect booking relationships','database.py',40,51,
    'Foreign keys require an existing flight and passenger. UNIQUE prevents duplicate seats and duplicate passenger bookings on the same flight.','Aben Batyr')

code_slide('Initial data: created only once','database.py',61,65,
    'seed() stops if any table contains records. A fully empty database receives 20 flights, 50 passengers and 40 tickets; random uses a fixed seed.','Aben Batyr')

terminal('Start with the main menu','17.56.11','Run: python3 main.py',
    'Choose an operation from 1 to 7. The menu repeats after each action; 0 exits the program.')

terminal('1. Add a flight','17.57.39','Result: flight 21 • KC900 • 90 seats • 45,000 KZT',
    'Add information → Flight. The user enters the route, departure, capacity and price. The program confirms the new flight ID.')

code_slide('Code: validate and save the flight','airline.py',62,70,
    'add_flight() validates the supplied fields, then inserts them. The question marks receive values separately; execute() commits and returns the new ID.','Abduldinov Alibek')

terminal('2. Add a passenger','17.58.28','Result: passenger 51 • Lena Luka',
    'Add information → Passenger. The name and email are saved as a passenger record. The generated ID is used when booking tickets.')

code_slide('Code: validate passenger details','airline.py',55,60,
    'required_text() rejects empty input. Email is converted to lowercase; re.fullmatch() checks its format. add_passenger() then saves the validated values.','Abduldinov Alibek')

def terminal_crop(time, name, box):
    original=ROOT/'docs/screenshots'/f'Screenshot 2026-10-18 at {time}.png'
    im=Image.open(original)
    w,h=im.size
    cropped=im.crop((round(box[0]*w),round(box[1]*h),round(box[2]*w),round(box[3]*h)))
    path=ASSETS/f'{name}.png'
    cropped.save(path)
    return path

new('3. Book a ticket: open the form','Choose 1 — Add information, then 3 — Ticket.',
    'Kushekbayev Batyrlan','The user selects Add information and Ticket. The program displays saved flights and passengers before asking for their IDs. These screenshots were taken after the earlier successful booking; they explain where the IDs come from.')
selection=terminal_crop('18.48.38','ticket_menu',(0,.24,1,.395))
flight_header=terminal_crop('18.48.38','flight_header',(0,.395,1,.451))
flight_row=terminal_crop('18.48.38','selected_flight',(0,.962,1,.993))
text(42,150,876,'STEP 1 / Select the operation',19,TEAL,bold=True)
image_file(selection,42,183,590,145)
text(42,337,876,'STEP 2 / Find the flight in the displayed table',19,TEAL,bold=True)
image_file(flight_header,42,371,876,45)
image_file(flight_row,42,414,876,28)
text(42,458,876,'Flight KC900 has ID 21 → enter 21 at the Flight ID prompt.',18,MUTED)

new('3. Book a ticket: choose the passenger','Use the ID column, not the passenger name or the row position.',
    'Kushekbayev Batyrlan','The passenger table is displayed after the flights. Passenger 51 is Lena Nika in this later screenshot because the name has already been updated. The ID remains 51, and that ID is used in the booking example.')
passenger_header=terminal_crop('18.48.49','passenger_header',(0,0,1,.112))
passenger_row=terminal_crop('18.49.16','selected_passenger',(0,.875,1,.981))
text(42,154,876,'STEP 3 / Find the passenger in the displayed table',19,TEAL,bold=True)
image_file(passenger_header,42,195,876,65)
image_file(passenger_row,42,271,876,62)
text(42,355,876,'Passenger ID = 51',27,TEAL,bold=True)
text(42,401,876,'Next: enter Flight ID 21, Passenger ID 51 and an available seat.',19)
text(42,447,876,'The name is Lena Nika after the update; the passenger ID stays 51.',17,MUTED)

terminal('3. Book a ticket: save the booking','18.45.22','Result: ticket 43 • flight 21 • passenger 51 • seat 2',
    'Seat 1 is already booked. Passenger 51 selects available seat 2 on flight 21. The program saves the booking and returns ticket ID 43.')

code_slide('Code: check the seat before saving','airline.py',78,93,
    'check_booking() checks IDs, the seat range, occupied seats and repeat passenger bookings. A conflict raises ValueError; otherwise the flight is returned.','Abduldinov Alibek')

code_slide('Code: save the ticket and its price','airline.py',102,108,
    'add_ticket() runs the checks, then stores the flight, passenger, seat and current price. Later changes to the flight price do not alter this ticket price.','Abduldinov Alibek')

terminal('4. Search for a passenger','18.01.01','Query: Lena → passenger 51, Lena Luka',
    'Search → Passenger by name or ID. A partial name is enough; matching is case-insensitive. The result displays ID, name and email.')

terminal('5. Search flights by destination','18.01.24','Query: Karaganda → flight KC900, one booked seat',
    'Search → Flights by destination. The result shows the route, departure, capacity, price and number of booked tickets.')

new('Code: search and handle missing records','Passenger search uses SQL; the display function handles an empty result.',
    'Abduldinov Alibek','The SQL matches either an exact ID or part of a name. An empty result is shown as No records found.')
image_file(source_image('airline.py',130,137),42,145,876,163)
image_file(ROOT/'docs/screenshots/Screenshot 2026-10-18 at 18.01.44.png',42,322,360,145)
text(430,342,488,'CAST compares ID as text.\ncasefold ignores letter case.\ninstr finds part of a name.\nEmpty rows → No records found.',18,MUTED)

terminal('6. Update a passenger','18.02.30','Passenger 51: Lena Luka → Lena Nika',
    'Update → Passenger. The program shows the old record, accepts replacement fields and confirms the update. airline.py: update_passenger() runs UPDATE.')

terminal('7. Cancel a ticket','18.03.53','Result: ticket 41 deleted after confirmation',
    'Delete or cancel → Ticket → ID 41 → yes. This is a separate ticket on flight 1, not ticket 43 from the booking example. delete_record() removes it.')

new('8. Calculate results and export','Recorded session: statistics before cancellation, then export through option 7.',
    'Abduldinov Alibek','Revenue sums active ticket prices. Occupancy is ticket count divided by total capacity. The captured statistics precede cancellation. Export writes all records and metrics to results.txt.')
image_file(ROOT/'docs/screenshots/Screenshot 2026-10-18 at 18.02.44.png',42,145,460,215)
text(530,158,385,'Revenue = SUM(ticket prices)',20,TEAL,bold=True)
text(530,203,385,'2,494,000 KZT',27,bold=True)
text(530,254,385,'Occupancy = 42 / 1601 × 100',19,TEAL)
text(530,291,385,'2.62%',27,bold=True)
image_file(ROOT/'docs/screenshots/Screenshot 2026-10-18 at 18.02.59.png',42,376,876,54)
text(42,445,876,'statistics() calculates metrics; export_results() saves records and results.txt.',17,MUTED)

new('Our contributions and what we learned','Two classes • three related tables • CRUD • search • calculations • file export',
    'All team members','Batyrlan presents the console interface; Batyr presents storage and generated data; Alibek presents booking rules, validation, calculations and export. Additional features are re and random.')
team=json.loads((ROOT/'docs/report_assets/team.json').read_text())
for y,member,module,desc in [(150,team['members'][1],'main.py','Menu, input, tables and error messages'),(246,team['members'][2],'database.py','SQLite, relationships and random data'),(342,team['members'][0],'airline.py','Booking, re validation, search and results')]:
    rect(42,y,876,80)
    text(58,y+14,340,member['name'],22,bold=True)
    text(420,y+10,470,module,18,TEAL,bold=True)
    text(420,y+42,470,desc,17,MUTED)
text(42,449,876,'Next: live demonstration and questions.',20,TEAL)

pdf.save()
prs.save(ROOT/'ProjectPresentation.pptx')
(ROOT/'docs/presentation_notes.md').write_text('# Presentation speaker notes\n\n'+'\n'.join(notes))
reopened=Presentation(ROOT/'ProjectPresentation.pptx')
assert len(reopened.slides)==22
assert all(s.notes_slide.notes_text_frame.text for s in reopened.slides)
print('Rebuilt 22-slide presentation and PDF.')
