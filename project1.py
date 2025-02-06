#!/usr/bin/python3
# alc24 - 24 - project1 
# DO NOT remove or edit the lines above. Thank you.
from datetime import datetime, timedelta
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF, IDPool
from pysat.card import CardEnc, EncType
import sys


def main():
    # Read the instructions from the file
    flights, code_with_stays, code_to_name, base = read_instructions()
    
    # Create clauses and solve the problem
    flying_tourist_problem(flights, code_with_stays, code_to_name, base)


# Get the date of the flight
def get_date(flight):
        return flight['date']


# Create dictionaries of flights by city (arrival and departure) and date
def create_dicts(flights):
    flights_by_city = {}
    flights_by_date = {}

    for i in flights:

        # If the city is not in the dictionary, add it
        if "from_" + i['orig'] not in flights_by_city:
            flights_by_city["from_" + i['orig']] = []

        # If the city is not in the dictionary, add it
        if "to_" + i['dest'] not in flights_by_city:
            flights_by_city["to_" + i['dest']] = []

        if i['date'] not in flights_by_date:
            flights_by_date[i['date']] = []

        # Add the flights to from_city and to_city keywords
        flights_by_city["from_" + i['orig']].append(i)
        flights_by_city["to_" + i['dest']].append(i)

        # Add the flight to the date keyword
        flights_by_date[i['date']].append(i)

    return flights_by_city, flights_by_date


def flying_tourist_problem(flights, code_with_stays, code_to_name, base):

    # Create the SAT solver
    solver = RC2(WCNF(), solver='g4', adapt=True, exhaust=True, minz=True)

    # Id pool for bitwise encoding
    vpool = IDPool()

    # Dictionary of flight ids
    flight_ids = {}

    # Get the last date with flights
    last_date = max(map(get_date, flights))    

    # Remove flights from base that exceed the last date
    for flight in flights:
        if flight['orig'] == base and flight['date'] + timedelta(days=sum(code_with_stays.values())) > last_date:
            if flight in flights:
                flights.remove(flight)

        if flight['date'] + timedelta(days=code_with_stays[flight['dest']]) > last_date:
            if flight in flights:
                flights.remove(flight)

    # Create a dictionaries
    flights_by_city, flights_by_date = create_dicts(flights)

    # Remove flights that exceed the last date
    for i in flights:
        if i['date'] + timedelta(days=code_with_stays[i['dest']]) in flights_by_date.keys() and i['dest'] != base:
            arrivals = []
            for j in flights_by_date[i['date'] + timedelta(days=code_with_stays[i['dest']])]:
                arrivals.append(j['orig'])

            if i['dest'] not in arrivals and i in flights and i['dest'] != base:
                flights.remove(i)

    # Create dictionaries again with filtered flights
    flights_by_city, flights_by_date = create_dicts(flights)

    # Add flight ids to the dictionary
    for i in flights:
        flight_ids[f"{i['date']}{i['orig']}{i['dest']}"] = vpool.id(f"{i['date']}{i['orig']}{i['dest']}")   


    ########################
    #     HARD CLAUSES     #
    ########################

    # Trip starts and ends to base city
    for flight in flights_by_city["from_" + base]:
        last_date = flight['date'] + timedelta(days=sum(code_with_stays.values()))

        if last_date in flights_by_date:
            flights_last_date = set([flight_ids[f"{j['date']}{j['orig']}{j['dest']}"] for j in flights_by_date[last_date]])
            flights_to_base = set([flight_ids[f"{j['date']}{j['orig']}{j['dest']}"] for j in flights_by_city["to_" + base]])

            next_flights = list(flights_last_date & flights_to_base)
            solver.add_clause([-(flight_ids[f"{flight['date']}{flight['orig']}{flight['dest']}"])] + next_flights)

    # The tourist arrives and departs from each city only once
    for i in flights_by_city.values():
        lits = [flight_ids[f"{j['date']}{j['orig']}{j['dest']}"] for j in i]
        cnf = CardEnc.equals(lits=lits, bound=1, vpool=vpool, encoding=EncType.bitwise)

        for clause in cnf.clauses:
            solver.add_clause(clause)

    # For each city the tourist stays exactly the number of nights from code_with_stays
    for flight in flights:
        if flight['dest'] != base:
            next_date = flight['date'] + timedelta(days=code_with_stays[flight['dest']])

            if next_date in flights_by_date:
                flights_next_date = set([flight_ids[f"{j['date']}{j['orig']}{j['dest']}"] for j in flights_by_date[next_date]])
                flights_to = set([flight_ids[f"{j['date']}{j['orig']}{j['dest']}"] for j in flights_by_city["from_" + flight['dest']]])

                next_flights = list(flights_next_date & flights_to)
                solver.add_clause([(-(flight_ids[f"{flight['date']}{flight['orig']}{flight['dest']}"]))] + next_flights)
            else:
                solver.add_clause([-(flight_ids[f"{flight['date']}{flight['orig']}{flight['dest']}"])])


    ########################
    #     SOFT CLAUSES     #
    ########################

    # The total cost of plane tickets is minimized
    for flight in flights:
        solver.add_clause([-(flight_ids[f"{flight['date']}{flight['orig']}{flight['dest']}"])], weight=int(flight['price']))


    ########################
    #        SOLVER        #
    ########################

    # Solve the problem
    model = solver.compute()

    # If the model is empty, return
    if not model:
        return
    
    # Print the cost
    print(solver.cost)

    # Print the flights in the model
    for i in flights:
        if flight_ids[f"{i['date']}{i['orig']}{i['dest']}"] in model:
            flight = i
            date = flight['date'].strftime("%d/%m")
            origin = code_to_name[flight['orig']]
            destination = code_to_name[flight['dest']]
            dept_time = flight['dept_time']
            price = flight['price']
            print(f"{date} {origin} {destination} {dept_time} {price}")


# Read the instructions from the file
def read_instructions():
    code_with_stays = {}
    code_to_name = {}
    flights = []
    
    lines = sys.stdin.read().strip().splitlines()
    
    n = int(lines[0].split()[0])
    
    base = lines[1].split()[1]

    date_format = "%d/%m"
    for i in range(1, n + 1): 
        line = lines[i].split() 
        
        code_with_stays[line[1]] = int(line[2]) if len(line) == 3 else 0
        code_to_name[line[1]] = line[0]
     
    m = int(lines[n + 1].split()[0])

    for i in range(n + 2, n + 2 + m):
        line = lines[i].split()  
        
        flight = {
            'orig': line[1],
            'dest': line[2],
            'date': datetime.strptime(line[0], date_format),
            'dept_time': line[3],
            'price': int(line[5])  
            }
        flights.append(flight)

    return flights, code_with_stays, code_to_name, base


if __name__ == "__main__":
    main()