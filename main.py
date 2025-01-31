import argparse
import importlib
import concurrent.futures
import random
from os import name as os_name
from os import system as os_system
from os.path import abspath, join, dirname
import sys
import json
import copy

# Add the utils folder to the path
sys.path.append(join(dirname(abspath(__file__)), "utils"))

# Import the utils
import pygraphics
from classes import Card, Player

# Set the path of the file
path = dirname(abspath(__file__))

TIMEOUT = 10  # Time limit for the AI agent

parser = argparse.ArgumentParser(description="A Game of Thrones: Hand of the King")
parser.add_argument('--player1', metavar='p1', type=str, help="either human or an AI file", default='human')
parser.add_argument('--player2', metavar='p2', type=str, help="either human or an AI file", default='human')
parser.add_argument('-l', '--load', type=str, help="file containing starting board setup (for repeatability)", default=None)
parser.add_argument('-s', '--save', type=str, help="file to save board setup to", default=None)
parser.add_argument('-v', '--video', type=str, help="name of the video file to save", default=None)

def make_board():
    '''
    This function creates a random board for the game.

    Returns:
        cards (list): list of Card objects
        companion_cards (dict): dictionary of companion cards
    '''

    # Load the characters
    with open(join(path, "assets", "characters.json"), 'r') as file:
        characters = json.load(file)
    
    companion_cards = characters['Companion'] # Dictionary of companion cards

    # Remove the companion cards from the dictionary
    del characters['Companion']

    cards = [] # List to hold the cards

    for i in range(36):
        # Get a random character
        house = random.choice(list(characters.keys()))
        name = random.choice(characters[house])

        # Remove the character from the dictionary
        characters[house].remove(name)
        if len(characters[house]) == 0:
            del characters[house]
        
        card = Card(house, name, i)

        cards.append(card)

    return cards, companion_cards

def save_board(cards, filename='board'):
    '''
    This function saves the board to a file.

    Parameters:
        cards (list): list of Card objects
        filename (str): name of the file to save the board to
    '''

    cards_json = []

    for card in cards:
        card_json = {'house': card.get_house(), 'name': card.get_name(), 'location': card.get_location()}
        cards_json.append(card_json)

    with open(join(path, "boards", filename + ".json"), 'w') as file:
        json.dump(cards_json, file, indent=4)

def load_board(filename='board'):
    '''
    This function loads the board from a file.

    Parameters:
        filename (str): name of the file to load the board from

    Returns:
        cards (list): list of Card objects
        companion_cards (dict): dictionary of companion cards
    '''

    with open(join(path, "boards", filename + ".json"), 'r') as file:
        cards = json.load(file)
    
    cards = [Card(card['house'], card['name'], card['location']) for card in cards]

    with open(join(path, "assets", "characters.json"), 'r') as file:
        characters = json.load(file)
    
    companion_cards = characters['Companion'] # Dictionary of companion cards

    return cards, companion_cards

def find_varys(cards):
    '''
    This function finds the location of Varys on the board.

    Parameters:
        cards (list): list of Card objects

    Returns:
        varys_location (int): location of Varys
    '''

    varys = [card for card in cards if card.get_name() == 'Varys']

    varys_location = varys[0].get_location()

    return varys_location

def get_possible_moves(cards):
    '''
    This function gets the possible moves for the player.

    Parameters:
        cards (list): list of Card objects

    Returns:
        moves (list): list of possible moves
    '''

    # Get the location of Varys
    varys_location = find_varys(cards)

    # Get the row and column of Varys
    varys_row, varys_col = varys_location // 6, varys_location % 6

    moves = []

    # Get the cards in the same row or column as Varys
    for card in cards:
        if card.get_name() == 'Varys':
            continue

        row, col = card.get_location() // 6, card.get_location() % 6

        if row == varys_row or col == varys_col:
            moves.append(card.get_location())

    return moves

def calculate_winner(player1, player2):
    '''
    This function determines the winner of the game.

    Parameters:
        player1 (Player): player 1
        player2 (Player): player 2

    Returns:
        winner (int): 1 if player 1 wins, 2 if player 2 wins
    '''

    player1_banners = player1.get_banners()
    player2_banners = player2.get_banners()

    # Calculate the scores of the players
    player1_score = sum(player1_banners.values())
    player2_score = sum(player2_banners.values())

    if player1_score > player2_score:
        return 1
    
    elif player2_score > player1_score:
        return 2
    
    # If the scores are the same, whoever has the banner of the house with the most cards wins
    else:
        if player1_banners['Stark'] > player2_banners['Stark']:
            return 1
        
        elif player2_banners['Stark'] > player1_banners['Stark']:
            return 2
        
        elif player1_banners['Greyjoy'] > player2_banners['Greyjoy']:
            return 1
        
        elif player2_banners['Greyjoy'] > player1_banners['Greyjoy']:
            return 2
        
        elif player1_banners['Lannister'] > player2_banners['Lannister']:
            return 1
        
        elif player2_banners['Lannister'] > player1_banners['Lannister']:
            return 2
        
        elif player1_banners['Targaryen'] > player2_banners['Targaryen']:
            return 1
        
        elif player2_banners['Targaryen'] > player1_banners['Targaryen']:
            return 2
        
        elif player1_banners['Baratheon'] > player2_banners['Baratheon']:
            return 1
        
        elif player2_banners['Baratheon'] > player1_banners['Baratheon']:
            return 2
        
        elif player1_banners['Tyrell'] > player2_banners['Tyrell']:
            return 1
        
        elif player2_banners['Tyrell'] > player1_banners['Tyrell']:
            return 2
        
        elif player1_banners['Tully'] > player2_banners['Tully']:
            return 1
        
        elif player2_banners['Tully'] > player1_banners['Tully']:
            return 2

def find_card(cards, location):
    '''
    This function finds the card at the location.

    Parameters:
        cards (list): list of Card objects
        location (int): location of the card

    Returns:
        card (Card): card at the location
    '''

    for card in cards:
        if card.get_location() == location:
            return card

def house_card_count(cards, house):
    '''
    This function counts the number of cards of a house.

    Parameters:
        cards (list): list of Card objects
        house (str): house of the cards

    Returns:
        count (int): number of cards of the house
    '''

    count = 0

    for card in cards:
        if card.get_house() == house:
            count += 1
    
    return count

def make_move(cards, move, player):
    '''
    This function makes a move for the player.

    Parameters:
        cards (list): list of Card objects
        move (int): location of the card
        player (Player): player making the move
    
    Returns:
        house (str): house of the selected card
    '''

    # Get the location of Varys
    varys_location = find_varys(cards)

    # Find the row and column of Varys
    varys_row, varys_col = varys_location // 6, varys_location % 6

    # Get the row and column of the move
    move_row, move_col = move // 6, move % 6

    # Find the selected card
    selected_card = find_card(cards, move)
    
    removing_cards = []

    # Find the cards that should be removed
    for i in range(len(cards)):
        if cards[i].get_name() == 'Varys':
            varys_index = i
            continue
        
        # If the card is between Varys and the selected card and has the same house as the selected card
        if varys_row == move_row and varys_col < move_col:
            if cards[i].get_location() // 6 == varys_row and varys_col < cards[i].get_location() % 6 < move_col and cards[i].get_house() == selected_card.get_house():
                removing_cards.append(cards[i])

                # Add the card to the player's cards
                player.add_card(cards[i])
        
        elif varys_row == move_row and varys_col > move_col:
            if cards[i].get_location() // 6 == varys_row and move_col < cards[i].get_location() % 6 < varys_col and cards[i].get_house() == selected_card.get_house():
                removing_cards.append(cards[i])

                # Add the card to the player's cards
                player.add_card(cards[i])
        
        elif varys_col == move_col and varys_row < move_row:
            if cards[i].get_location() % 6 == varys_col and varys_row < cards[i].get_location() // 6 < move_row and cards[i].get_house() == selected_card.get_house():
                removing_cards.append(cards[i])

                # Add the card to the player's cards
                player.add_card(cards[i])
        
        elif varys_col == move_col and varys_row > move_row:
            if cards[i].get_location() % 6 == varys_col and move_row < cards[i].get_location() // 6 < varys_row and cards[i].get_house() == selected_card.get_house():
                removing_cards.append(cards[i])

                # Add the card to the player's cards
                player.add_card(cards[i])
    
    # Add the selected card to the player's cards
    player.add_card(selected_card)

    # Set the location of Varys
    cards[varys_index].set_location(move)
        
    # Remove the cards
    for card in removing_cards:
        cards.remove(card)
    
    # Remove the selected card
    cards.remove(selected_card)

    # Return the selected card's house
    return selected_card.get_house()

def make_companion_move(cards, companion_cards, move, player):
    '''
    This function makes the move of the companion card.

    Parameters:
        cards (list): list of Card objects
        companion_cards (dict): dictionary of companion cards
        move (int): location of the card
        player (Player): player making the move
    
    Returns:
        house (str/None): house of the selected card
    '''

    selected_companion = move[0] # Selected companion card
    house = None # House of the selected card

    if selected_companion == 'Jon':
        selected_card = move[1]

        # Find the selected card
        selected_card = find_card(cards, selected_card)

        # Get the house of the selected card
        selected_house = selected_card.get_house()

        house = selected_house # Set the house

        # Make a card
        card = Card(selected_house, 'Jon Snow', -1)

        # Add the card to the player's cards two times
        player.add_card(card)
        player.add_card(card)
    
    elif selected_companion == 'Gendry':
        # Make a card of the house Baratheon
        card = Card('Baratheon', 'Gendry', -1)

        house = 'Baratheon' # Set the house

        # Add the card to the player's cards
        player.add_card(card)
    
    elif selected_companion == 'Ramsay':
        first_card = move[1]
        second_card = move[2]

        # Find the selected cards
        first_card = find_card(cards, first_card)
        second_card = find_card(cards, second_card)

        # Swap the locations of the cards
        temp_location = first_card.get_location()
        first_card.set_location(second_card.get_location())
        second_card.set_location(temp_location)
    
    elif selected_companion == 'Sandor':
        selected_card = move[1]

        # Find the selected card
        selected_card = find_card(cards, selected_card)

        # Remove the selected card from the cards
        cards.remove(selected_card)
    
    elif selected_companion == 'Jaqen':
        first_card = move[1]
        second_card = move[2]
        selected_companion_card = move[3]

        # Find the selected cards
        first_card = find_card(cards, first_card)
        second_card = find_card(cards, second_card)

        # Remove the selected cards from the cards
        cards.remove(first_card)
        cards.remove(second_card)

        # Remove the selected companion card from the companion cards
        del companion_cards[selected_companion_card]
    
    return house

def remove_unusable_companion_cards(cards, companion_cards):
    '''
    This function removes the companion cards that cannot be used.

    Parameters:
        cards (list): list of Card objects
        companion_cards (dict): dictionary of companion cards
    '''

    # Get the possible moves for the player
    moves = get_possible_moves(cards)

    if 'Ramsay' in companion_cards.keys() and len(cards) < 2: # Ramsay needs at least two cards to swap
        del companion_cards['Ramsay']
    
    if 'Melisandre' in companion_cards.keys() and len(moves) == 0: # If there are no moves left, there is no point in using Melisandre
        del companion_cards['Melisandre']

    for companion in list(companion_cards.keys()):
        if companion_cards[companion]['Choice'] > len(cards) - 1: # If the number of choices is more than the number of cards
            del companion_cards[companion]
    
    if 'Jaqen' in companion_cards.keys() and len(companion_cards) == 1: # If Jaqen is the only companion card left
        del companion_cards['Jaqen']

def set_banners(player1, player2, last_house, last_turn):
    '''
    This function sets the banners for the players.

    Parameters:
        player1 (Player): player 1
        player2 (Player): player 2
        last_house (str): house of the last chosen card
        last_turn (int): last turn of the player

    Returns:
        player1_status (dict): status of the cards for player 1
        player2_status (dict): status of the cards for player 2
    '''

    # Get the cards of the players
    player1_cards = player1.get_cards()
    player2_cards = player2.get_cards()

    # Get the banners of the players
    player1_banners = player1.get_banners()
    player2_banners = player2.get_banners()

    # Initialize the status of the cards
    player1_status = {}
    player2_status = {}

    for house in player1_cards.keys():
        # Flag to keep track of the selected player
        selected_player = None

        # The player with the more cards of a house gets the banner
        if len(player1_cards[house]) > len(player2_cards[house]):
            # Give the banner to player 1
            selected_player = 1

        elif len(player2_cards[house]) > len(player1_cards[house]):
            # Give the banner to player 2
            selected_player = 2

        # If the number of cards is the same, the player who chose the last card of that house gets the banner
        else:
            if last_house == house:
                if last_turn == 1:
                    # Give the banner to player 1
                    selected_player = 1

                else:
                    # Give the banner to player 2
                    selected_player = 2

            else: # If the last card was not of the same house
                if player1_banners[house] > player2_banners[house]: # If player 1 has more banners of the house
                    selected_player = 1
                
                elif player2_banners[house] > player1_banners[house]: # If player 2 has more banners of the house
                    selected_player = 2

        # If player 1 should get the banner
        if selected_player == 1:
            # Give the banner to player 1
            player1.get_house_banner(house)
            player2.remove_house_banner(house)

            # Set the status of the cards
            if len(player1_cards[house]) != 0:
                player1_status[house] = len(player1_cards[house]), 'Green'

            else:
                player1_status[house] = len(player1_cards[house]), 'White'

            player2_status[house] = len(player2_cards[house]), 'White'

        elif selected_player == 2:
            # Give the banner to player 2
            player1.remove_house_banner(house)
            player2.get_house_banner(house)

            # Set the status of the cards
            if len(player2_cards[house]) != 0:
                player2_status[house] = len(player2_cards[house]), 'Green'

            else:
                player2_status[house] = len(player2_cards[house]), 'White'

            player1_status[house] = len(player1_cards[house]), 'White'

        else: # If no player has the banner
            player2_status[house] = len(player2_cards[house]), 'White'
            player1_status[house] = len(player1_cards[house]), 'White'

    return player1_status, player2_status

def clear_screen():
    '''
    This function clears the screen.
    '''

    if os_name == 'nt': # Windows
        os_system('cls')
    
    else: # Mac and Linux
        os_system('clear')

def print_cards_status(player1_status, player2_status):
    '''
    This function prints the status of cards of the players.

    Parameters:
        player1_status (dict): status of the cards for player 1
        player2_status (dict): status of the cards for player 2
    '''

    # Clear the screen
    clear_screen()

    # Print the status of the cards
    print("Player 1 cards status:", end=' ')
    for house, status in player1_status.items():
        try:
            # If player 1 has the banner of the house
            if status[1] == 'Green':
                # Print the house in color green
                print(f"\033[92m{house}: {status[0]}\033[0m", end=' ')
            
            else:
                # Print the house in color white
                print(f"\033[97m{house}: {status[0]}\033[0m", end=' ')
        
        except:
            print(f"{house}: {status[0]}", end=' ')
    
    # Print a new line
    print()

    print("Player 2 cards status:", end=' ')
    for house, status in player2_status.items():
        try:
            # If player 2 has the banner of the house
            if status[1] == 'Green':
                # Print the house in color green
                print(f"\033[92m{house}: {status[0]}\033[0m", end=' ')
            
            else:
                # Print the house in color white
                print(f"\033[97m{house}: {status[0]}\033[0m", end=' ')
        
        except:
            print(f"{house}: {status[0]}", end=' ')
    
    # Print a new line
    print()

def validate_agent_move(cards, companion_cards, given_move):
    '''
    This function validates the move of the AI agent.

    Parameters:
        cards (list): list of Card objects
        companion_cards (dict): dictionary of remaining companion cards
        given_move (int): move from the AI agent

    Returns:
        valid (bool): True if the move is valid, False otherwise
    '''

    # Check if the selected companion card is valid
    if given_move[0] not in companion_cards.keys():
        return False
    
    # Get the choices of the companion card
    choices = companion_cards[given_move[0]]['Choice']

    # Check if the number of choices is valid
    if len(given_move) - 1 != choices:
        return False
    
    # Check if Jaqen is selected with another companion card not himself
    if given_move[0] == 'Jaqen' and given_move[0] == given_move[-1]:
        return False
    
    number_of_occurrences = {} # Dictionary to keep track of the number of occurrences of the selected locations

    # Get all possible locations
    locations = []

    for card in cards:
        if card.get_name() == 'Varys' and given_move[0] == 'Ramsay':
            locations.append(card.get_location())
        
        elif card.get_name() != 'Varys':
            locations.append(card.get_location())
    
    loop_size = len(given_move) if given_move[0] != 'Jaqen' else len(given_move) - 1
    
    # Check if the selected cards are valid
    for i in range(1, loop_size):
        if given_move[i] not in locations:
            return False
        
        if given_move[i] in number_of_occurrences.keys():
            return False
        
        number_of_occurrences[given_move[i]] = 1 # Add the location to the dictionary
    
    return True # All checks passed

def try_get_move(agent, cards, player1, player2, companion_cards, choose_companion):
    '''
    This function tries to get the move from the AI agent.

    Parameters:
        agent (module): AI agent
        cards (list): list of Card objects
        player1 (Player): player 1
        player2 (Player): player 2
        companion_cards (dict): dictionary of companion cards
        choose_companion (bool): flag to choose a companion card

    Returns:
        move (int/list): move from the AI agent
    '''
    
    # Try to get the move from the AI agent in TIMEOUT seconds
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(agent.get_move, copy.deepcopy(cards), copy.deepcopy(player1),
                                 copy.deepcopy(player2), copy.deepcopy(companion_cards), choose_companion)

        try:
            move = future.result(timeout=TIMEOUT)
        
        except concurrent.futures.TimeoutError:
            move = None
    
    return move
            
def main(args):
    '''
    This function runs the game.

    Parameters:
        args (Namespace): command line arguments
    '''

    if args.load:
        try:
            # Load the board from the file
            cards, companion_cards = load_board(args.load)
        
        except FileNotFoundError:
            print("File not found. Creating a new board.")
            cards, companion_cards = make_board()
    
    else:
        # Create a new board
        cards, companion_cards = make_board()
    
    if args.save:
        try:
            # Save the board to the file
            save_board(cards, args.save)
        
        except:
            print("Error saving board.")
    
    # Set up the graphics
    board = pygraphics.init_board()

    # Clear the screen
    clear_screen()

    # Draw the board
    pygraphics.draw_board(board, cards, companion_cards,  '0', None)

    # Show the initial board for 2 seconds
    pygraphics.show_board(2)

    # Check if the players are human or AI
    if args.player1 == 'human':
        player1_agent = None
    
    else:
        # Check if the AI file exists
        try:
            player1_agent = importlib.import_module(args.player1)
        
        except ImportError:
            print("AI file not found.")
            return
        
        if not hasattr(player1_agent, 'get_move'):
            print("AI file does not have the get_move function.")
            return
    
    if args.player2 == 'human':
        player2_agent = None
    
    else:
        # Check if the AI file exists
        try:
            player2_agent = importlib.import_module(args.player2)
        
        except ImportError:
            print("AI file not found.")
            return
        
        if not hasattr(player2_agent, 'get_move'):
            print("AI file does not have the get_move function.")
            return
    
    # Set up the players
    player1 = Player(args.player1)
    player2 = Player(args.player2)

    # Set up the turn
    turn = 1 # 1: player 1's turn, 2: player 2's turn

    # Draw the board
    pygraphics.draw_board(board, cards, companion_cards, '1')

    # Set Choose Companion flag
    choose_companion = False

    while True:
        # Get the possible moves for the player
        moves = get_possible_moves(cards)

        # Check if the player has no moves left to make
        if (len(moves) == 0 and ((not choose_companion) or (len(companion_cards) == 0))):
            # Get the winner of the game
            winner = calculate_winner(player1, player2)
            
            # Display the winner
            pygraphics.display_winner(board, winner, player1.get_agent() if winner == 1 else player2.get_agent())

            # Show the board for 5 seconds
            pygraphics.show_board(5)

            break

        # Get the player's move
        if turn == 1:
            # Check if the player is human or AI
            if player1_agent is None:
                # Wait for the player to make a move with the mouse
                move = pygraphics.get_player_move(moves, companion_cards if choose_companion else None)
            
            else:
                # Get the move from the AI agent
                move = try_get_move(player1_agent, cards, player1, player2, companion_cards, choose_companion)

                # If the move is None, change the turn
                if move is None:
                    turn = 2
                    continue
        
        else:
            # Check if the player is human or AI
            if player2_agent is None:
                # Wait for the player to make a move with the mouse
                move = pygraphics.get_player_move(moves, companion_cards if choose_companion else None)
            
            else:
                # Get the move from the AI agent
                move = try_get_move(player2_agent, cards, player1, player2, companion_cards, choose_companion)

                # If the move is None, change the turn
                if move is None:
                    turn = 1
                    continue
        
        # If the move is companion card
        if choose_companion:
            # Check if the move is valid
            if move[0] in companion_cards.keys():
                choices = companion_cards[move[0]]['Choice'] # Number of choices for the companion card

                # If the player is human, get the selected cards
                if (turn == 1 and player1_agent is None) or (turn == 2 and player2_agent is None):
                    selectable_cards = [] # List to hold the selectable cards
                    selectable_companion_cards = {key: value for key, value in companion_cards.items() if key != move[0]} # Dictionary to hold the selectable companion cards

                    for card in cards:
                        if card.get_name() == 'Varys' and move[0] == 'Ramsay': # Ramsay can change the location of two cards
                            selectable_cards.append(card.get_location())
                        
                        elif card.get_name() != 'Varys':
                            selectable_cards.append(card.get_location())

                    for i in range(choices):
                        # Condition for selecting a companion card
                        companion_selecting_condition = (move[0] == 'Jaqen' and i + 1 == choices)

                        # Set the footer's text
                        footer_text = 'CC' if companion_selecting_condition else f'BC{i + 1}'

                        # Draw the board
                        if turn == 1:
                            pygraphics.draw_board(board, cards, selectable_companion_cards, footer_text, companion_selecting_condition)
                        
                        else:
                            pygraphics.draw_board(board, cards, selectable_companion_cards, footer_text, companion_selecting_condition)

                        # Wait for the player to make a move with the mouse
                        selected = pygraphics.get_player_move(selectable_cards, selectable_companion_cards if companion_selecting_condition else None)

                        if not companion_selecting_condition:
                            selectable_cards.remove(selected) # Remove the selected card from the list
                        
                        else:
                            selected = selected[0] # Get the selected card

                        move.append(selected) # Add the selected card to the list

                elif not validate_agent_move(cards, companion_cards, move):
                    continue

                # Remove the companion card from the list
                del companion_cards[move[0]]

                # Make the companion move
                is_house = make_companion_move(cards, companion_cards, move, player1 if turn == 1 else player2)

                # Remove the companion cards that cannot be used
                remove_unusable_companion_cards(cards, companion_cards)

                # Set the banners for the players
                player1_status, player2_status = set_banners(player1, player2, is_house if is_house is not None else selected_house, turn)

                # Print the status of the cards
                print_cards_status(player1_status, player2_status)

                # Melisandre gives the player another turn
                if move[0] != 'Melisandre':
                    # Change the turn
                    turn = 2 if turn == 1 else 1

                choose_companion = False # Reset the flag

            # Draw the board
            if turn == 1:
                pygraphics.draw_board(board, cards, companion_cards, '1', choose_companion)
            
            else:
                pygraphics.draw_board(board, cards, companion_cards, '2', choose_companion)
            
            # Show the board for 0.5 seconds
            pygraphics.show_board(0.5)

        # Check if the move is valid
        if move in moves:
            # Make the move
            selected_house = make_move(cards, move, player1 if turn == 1 else player2)

            # Remove the companion cards that cannot be used
            remove_unusable_companion_cards(cards, companion_cards)

            # Set the banners for the players
            player1_status, player2_status = set_banners(player1, player2, selected_house, turn)

            # Print the status of the cards
            print_cards_status(player1_status, player2_status)

            # If there are no cards of the house and there are companion cards left
            if house_card_count(cards, selected_house) == 0 and len(companion_cards) != 0:
                choose_companion = True # Player must choose a companion card
            
            else:
                # Change the turn
                turn = 2 if turn == 1 else 1

                choose_companion = False # Reset the flag

            # Draw the board
            if turn == 1:
                pygraphics.draw_board(board, cards, companion_cards, 'CC' if choose_companion else '1', choose_companion)
            
            else:
                pygraphics.draw_board(board, cards, companion_cards, 'CC' if choose_companion else '2', choose_companion)
            
            # Show the board for 0.5 seconds
            pygraphics.show_board(0.5)
    
    # Close the board
    pygraphics.close_board()

    file_name = args.video # Name of the video file

    if file_name is None: # If not provided
        # Set the name of the video file as Agent1_vs_Agent2
        if player1.get_agent() != 'human':
            file_name = player1.get_agent()[max(0, player1.get_agent().find('/'), player1.get_agent().find('\\')):]
        
        else:
            file_name = player1.get_agent()
        
        file_name += '_vs_'

        if player2.get_agent() != 'human':
            file_name += player2.get_agent()[max(0, player2.get_agent().find('/'), player2.get_agent().find('\\')):]
        
        else:
            file_name += player2.get_agent()
    
    try:
        pygraphics.save_video(file_name) # Save the video of the game
    
    except:
        print("Error saving video.")

if __name__ == "__main__":
    main(parser.parse_args())