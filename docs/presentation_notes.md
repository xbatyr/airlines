# Presentation speaker notes

## Slide 1: Airline Reservation System

Presenter: All team members

We will demonstrate the app in the terminal and explain the exact source code behind its actions.

## Slide 2: Three modules, one workflow

Presenter: All team members

main.py handles input and output. AirlineSystem handles application rules. Database handles storage.

## Slide 3: How the tables are connected

Presenter: Aben Batyr

Flights and passengers each have many tickets. Tickets implement the many-to-many relationship between them.

## Slide 4: Database: protect booking relationships

Presenter: Aben Batyr

Foreign keys require an existing flight and passenger. UNIQUE prevents duplicate seats and duplicate passenger bookings on the same flight.

## Slide 5: Initial data: created only once

Presenter: Aben Batyr

seed() stops if any table contains records. A fully empty database receives 20 flights, 50 passengers and 40 tickets; random uses a fixed seed.

## Slide 6: Start with the main menu

Presenter: Kushekbayev Batyrlan

Choose an operation from 1 to 7. The menu repeats after each action; 0 exits the program.

## Slide 7: 1. Add a flight

Presenter: Kushekbayev Batyrlan

Add information → Flight. The user enters the route, departure, capacity and price. The program confirms the new flight ID.

## Slide 8: Code: validate and save the flight

Presenter: Abduldinov Alibek

add_flight() validates the supplied fields, then inserts them. The question marks receive values separately; execute() commits and returns the new ID.

## Slide 9: 2. Add a passenger

Presenter: Kushekbayev Batyrlan

Add information → Passenger. The name and email are saved as a passenger record. The generated ID is used when booking tickets.

## Slide 10: Code: validate passenger details

Presenter: Abduldinov Alibek

required_text() rejects empty input. Email is converted to lowercase; re.fullmatch() checks its format. add_passenger() then saves the validated values.

## Slide 11: 3. Book a ticket: open the form

Presenter: Kushekbayev Batyrlan

The user selects Add information and Ticket. The program displays saved flights and passengers before asking for their IDs. These screenshots were taken after the earlier successful booking; they explain where the IDs come from.

## Slide 12: 3. Book a ticket: choose the passenger

Presenter: Kushekbayev Batyrlan

The passenger table is displayed after the flights. Passenger 51 is Lena Nika in this later screenshot because the name has already been updated. The ID remains 51, and that ID is used in the booking example.

## Slide 13: 3. Book a ticket: save the booking

Presenter: Kushekbayev Batyrlan

Seat 1 is already booked. Passenger 51 selects available seat 2 on flight 21. The program saves the booking and returns ticket ID 43.

## Slide 14: Code: check the seat before saving

Presenter: Abduldinov Alibek

check_booking() checks IDs, the seat range, occupied seats and repeat passenger bookings. A conflict raises ValueError; otherwise the flight is returned.

## Slide 15: Code: save the ticket and its price

Presenter: Abduldinov Alibek

add_ticket() runs the checks, then stores the flight, passenger, seat and current price. Later changes to the flight price do not alter this ticket price.

## Slide 16: 4. Search for a passenger

Presenter: Kushekbayev Batyrlan

Search → Passenger by name or ID. A partial name is enough; matching is case-insensitive. The result displays ID, name and email.

## Slide 17: 5. Search flights by destination

Presenter: Kushekbayev Batyrlan

Search → Flights by destination. The result shows the route, departure, capacity, price and number of booked tickets.

## Slide 18: Code: search and handle missing records

Presenter: Abduldinov Alibek

The SQL matches either an exact ID or part of a name. An empty result is shown as No records found.

## Slide 19: 6. Update a passenger

Presenter: Kushekbayev Batyrlan

Update → Passenger. The program shows the old record, accepts replacement fields and confirms the update. airline.py: update_passenger() runs UPDATE.

## Slide 20: 7. Cancel a ticket

Presenter: Kushekbayev Batyrlan

Delete or cancel → Ticket → ID 41 → yes. This is a separate ticket on flight 1, not ticket 43 from the booking example. delete_record() removes it.

## Slide 21: 8. Calculate results and export

Presenter: Abduldinov Alibek

Revenue sums active ticket prices. Occupancy is ticket count divided by total capacity. The captured statistics precede cancellation. Export writes all records and metrics to results.txt.

## Slide 22: Our contributions and what we learned

Presenter: All team members

Batyrlan presents the console interface; Batyr presents storage and generated data; Alibek presents booking rules, validation, calculations and export. Additional features are re and random.
