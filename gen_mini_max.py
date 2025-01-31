import copy

# -------------------------------
#         HELPER FUNCTIONS
# -------------------------------

def find_varys(cards):
    """
    Returns the board location (0..35) of Varys.
    """
    for c in cards:
        if c.get_name() == "Varys":
            return c.get_location()
    return None

def get_valid_moves(cards):
    """
    Returns all valid moves for a normal turn (i.e. picking a card in the same row/column as Varys).
    """
    varys_location = find_varys(cards)
    if varys_location is None:
        return []

    varys_row, varys_col = divmod(varys_location, 6)
    moves = []
    for c in cards:
        if c.get_name() == "Varys":
            continue
        row, col = divmod(c.get_location(), 6)
        if row == varys_row or col == varys_col:
            moves.append(c.get_location())
    return moves

from itertools import combinations

def get_companion_moves(cards, companion_cards):
    """
    Generate *all* valid ways to use each available companion.
    Each returned move is a list, e.g. [ "Jon", cardLocation ],
    [ "Ramsay", loc1, loc2 ], [ "Jaqen", loc1, loc2, someCompanionName ], etc.
    """
    if not companion_cards:
        return []

    moves = []

    # Collect lists of possible board locations
    # For some companions (e.g. Ramsay) we include Varys; for others (e.g. Sandor) we exclude him.
    all_locations_non_varys = [c.get_location() for c in cards if c.get_name() != 'Varys']
    all_locations_including_varys = [c.get_location() for c in cards]  # needed by Ramsay

    for comp_name, comp_data in companion_cards.items():
        # The main game code often uses comp_data['Choice'] to see how many picks to gather,
        # but we also need the *type* of picks (e.g. one location, two, or removing a companion).
        # We'll do it manually below, keyed by companion name.
        
        if comp_name == 'Jon':
            # Must pick 1 board card (non-Varys). E.g. ["Jon", <card_loc>].
            for loc in all_locations_non_varys:
                moves.append([comp_name, loc])

        elif comp_name == 'Gendry':
            # No extra picks: just ["Gendry"].
            moves.append([comp_name])

        elif comp_name == 'Sandor':
            # Must pick 1 board card to remove (cannot remove Varys). E.g. ["Sandor", <card_loc>].
            for loc in all_locations_non_varys:
                moves.append([comp_name, loc])

        elif comp_name == 'Ramsay':
            # Pick 2 distinct cards (CAN include Varys). E.g. ["Ramsay", <loc1>, <loc2>].
            locs = all_locations_including_varys
            for loc1, loc2 in combinations(locs, 2):
                moves.append([comp_name, loc1, loc2])

        elif comp_name == 'Jaqen':
            # In the main code: ["Jaqen", loc1, loc2, someOtherCompanionName].
            #   - Remove two chosen cards from board (usually non-Varys).
            #   - Then remove a *different* companion from companion_cards.
            # The main code allows removing any two board cards,
            # but typically you'd skip Varys so you don't break the game.
            # Then the last parameter is a *different* companion’s name (since you remove it).
            other_companions = [cname for cname in companion_cards.keys()]
            # You can decide whether to forbid removing "Jaqen" itself; the main code checks
            # if (given_move[0] == 'Jaqen' and given_move[0] == given_move[-1]) => invalid.
            # We'll skip generating that to avoid immediate invalid moves.
            locs = all_locations_non_varys
            for loc1, loc2 in combinations(locs, 2):
                for other_comp in other_companions:
                    if other_comp == comp_name:  # skip picking the same "Jaqen" to remove
                        continue
                    moves.append([comp_name, loc1, loc2, other_comp])

        elif comp_name == 'Melisandre':
            # No extra picks: just ["Melisandre"].
            # She grants the same player a second turn in the main game logic.
            moves.append([comp_name])

        # If you have other custom companions, handle them similarly.

    return moves


def clone_game_state(cards, player1, player2):
    """
    Makes a deep copy of the game state (cards plus the two Players).
    Note: The 'cards' list contains Card objects, and each Player object
    has references to cards they've collected. We can do a shallow copy
    of Card objects if needed. This function attempts a deeper copy
    for safe minimax simulation.
    """
    new_cards = copy.deepcopy(cards)
    new_player1 = copy.deepcopy(player1)
    new_player2 = copy.deepcopy(player2)
    return new_cards, new_player1, new_player2

def make_normal_move(cards, move_location, current_player):
    """
    Applies a normal move by picking the card at 'move_location' in the same
    row/column as Varys.  This replicates (in a shortened manner) the logic
    from the main code for 'make_move'. Returns (house_chosen) so we can
    check if that house is exhausted, etc.
    """
    # Find Varys index and selected card index.
    varys_index = None
    selected_index = None
    for i, c in enumerate(cards):
        if c.get_name() == 'Varys':
            varys_index = i
        if c.get_location() == move_location:
            selected_index = i

    if varys_index is None or selected_index is None:
        return None  # Invalid

    varys_card = cards[varys_index]
    selected_card = cards[selected_index]
    house_chosen = selected_card.get_house()

    # Gather "in-between" cards that match the house, following main game logic:
    vrow, vcol = divmod(varys_card.get_location(), 6)
    srow, scol = divmod(move_location, 6)

    # Add the selected card to the player's holdings
    current_player.add_card(selected_card)

    # We'll track cards that will be removed from board
    removed_indices = [selected_index]

    # Check in-between
    for i, c in enumerate(cards):
        if i == varys_index or i == selected_index:
            continue
        row, col = divmod(c.get_location(), 6)
        if c.get_house() == house_chosen:
            # same row, varys_col < col < scol or scol < col < varys_col ...
            if vrow == srow:
                # horizontal move
                if row == vrow:
                    if vcol < scol and vcol < col < scol:
                        current_player.add_card(c)
                        removed_indices.append(i)
                    elif scol < vcol and scol < col < vcol:
                        current_player.add_card(c)
                        removed_indices.append(i)
            elif vcol == scol:
                # vertical move
                if col == vcol:
                    if vrow < srow and vrow < row < srow:
                        current_player.add_card(c)
                        removed_indices.append(i)
                    elif srow < vrow and srow < row < vrow:
                        current_player.add_card(c)
                        removed_indices.append(i)

    # Move Varys to the new location
    varys_card.set_location(move_location)

    # Remove cards in descending index order so as not to break indices as we pop
    for idx in sorted(removed_indices, reverse=True):
        if idx == varys_index:
            # don't remove Varys from the game, just skip
            continue
        del cards[idx]

    # Return the chosen house
    return house_chosen

def find_card(cards, location):
    """
    Utility function: find the Card object in 'cards' with a matching .get_location().
    Returns that Card or None if not found.
    """
    for c in cards:
        if c.get_location() == location:
            return c
    return None

def make_companion_move(cards, companion_cards, chosen_move, current_player):
    """
    Applies the effect of a chosen companion card.

    Parameters:
        cards (list): current list of Card objects on the board
        companion_cards (dict): dictionary of still-available companion cards
        chosen_move (list): the selected move, e.g.:
           [ "Jon", <card_location> ]
           [ "Ramsay", <card_location1>, <card_location2> ]
           [ "Jaqen", <card_location1>, <card_location2>, <another_companion> ]
           ... etc.
        current_player (Player): the player using the companion card

    Returns:
        house (str or None): If a companion effect effectively "captures" a particular House,
                             return that House so the caller can check if it is exhausted.
                             If no house is captured by this effect, return None.
    """

    selected_companion = chosen_move[0]   # e.g. "Jon", "Gendry", "Ramsay", "Sandor", "Jaqen", "Melisandre"
    house = None  # Will store a captured House (if relevant)

    if selected_companion == 'Jon':
        #
        # Jon Snow effect:
        # chosen_move = ["Jon", some_card_location]
        #
        #  - You (the current player) choose ANY single board card (not Varys)
        #  - That card’s house is "copied" twice into your holdings as "Jon Snow" cards.
        #
        # In the main code: 2 tokens of the same house are added to the player's deck.
        #
        selected_card_loc = chosen_move[1]
        target_card = find_card(cards, selected_card_loc)
        if target_card:
            target_house = target_card.get_house()
            house = target_house  # you effectively "chose" that house
            # Add two "Jon Snow" placeholders to your deck, each counting as that house
            from classes import Card
            for _ in range(2):
                card_placeholder = Card(house=target_house, name='Jon Snow', location=-1)
                current_player.add_card(card_placeholder)

    elif selected_companion == 'Gendry':
        #
        # Gendry effect:
        # chosen_move = ["Gendry"]
        #
        #  - Add one Baratheon card to your holdings (named "Gendry").
        #
        from classes import Card
        house = 'Baratheon'
        gendry_card = Card(house, 'Gendry', -1)
        current_player.add_card(gendry_card)

    elif selected_companion == 'Ramsay':
        #
        # Ramsay effect:
        # chosen_move = ["Ramsay", card_location1, card_location2]
        #
        #  - Swap the board locations of two different cards (can include Varys).
        #
        first_loc = chosen_move[1]
        second_loc = chosen_move[2]
        card1 = find_card(cards, first_loc)
        card2 = find_card(cards, second_loc)
        if card1 and card2:
            temp = card1.get_location()
            card1.set_location(card2.get_location())
            card2.set_location(temp)

    elif selected_companion == 'Sandor':
        #
        # Sandor Clegane effect:
        # chosen_move = ["Sandor", card_location]
        #
        #  - Permanently remove one card (non-Varys) from the board. 
        #
        target_loc = chosen_move[1]
        to_remove = find_card(cards, target_loc)
        if to_remove is not None and to_remove.get_name() != 'Varys':
            cards.remove(to_remove)

    elif selected_companion == 'Jaqen':
        #
        # Jaqen H'ghar effect:
        # chosen_move = ["Jaqen", card_location1, card_location2, some_other_companion_name]
        #
        #  - Remove two chosen cards from the board, then also remove
        #    any single companion card from the companion_cards (the last item of chosen_move).
        #    It can be another Jaqen or any other companion.
        #
        first_loc = chosen_move[1]
        second_loc = chosen_move[2]
        to_remove_companion_name = chosen_move[3]

        card1 = find_card(cards, first_loc)
        card2 = find_card(cards, second_loc)
        if card1 in cards: cards.remove(card1)
        if card2 in cards: cards.remove(card2)

        if to_remove_companion_name in companion_cards:
            del companion_cards[to_remove_companion_name]

    elif selected_companion == 'Melisandre':
        #
        # Melisandre effect (in main code, it gives you an immediate second turn).
        # Usually no direct board effect. The logic of "take another turn" is handled 
        # in your main loop if move[0] == 'Melisandre'.
        #
        # chosen_move = ["Melisandre"]
        #
        # No board manipulation. House remains None.
        pass

    # Finally, remove the used companion from the companion_cards dictionary.
    # (If a companion is "Jaqen" and you remove another companion, that other 
    #  companion is removed above. This removes the *chosen* companion.)
    if selected_companion in companion_cards:
        del companion_cards[selected_companion]

    return house

def count_player_cards(player):
    """
    Returns the total number of captured cards for a player.
    (One simple way to do an evaluation.)
    """
    all_cards = player.get_cards()  # This is a dict of {house: [cards]}
    total = 0
    for _, cards_list in all_cards.items():
        total += len(cards_list)
    return total

def evaluate_state(player1, player2):
    """
    Simple evaluation: difference in total captured cards = player1_cards - player2_cards.
    If positive, it's better for player1; if negative, better for player2.
    """
    # return count_player_cards(player1) - count_player_cards(player2)
    player1_cards = sum(len(cards) for cards in player1.get_cards().values())
    player2_cards = sum(len(cards) for cards in player2.get_cards().values())

    player1_banners = sum(player1.get_banners().values())
    player2_banners = sum(player2.get_banners().values())
    # score = (
    #     2 * (player1_cards - player2_cards) +
    #     1.5 * (player1_banners - player2_banners)
    # )
    score = (
        1.84 * (player1_cards - player2_cards) +
        2.96 * (player1_banners - player2_banners)
    )
    return score

# -------------------------------
#       MINIMAX SEARCH
# -------------------------------

def minimax(cards, player1, player2, companion_cards, choose_companion,
            depth, alpha, beta, maximizing_player):
    """
    Returns (best_score, best_move).

    - `cards, player1, player2, companion_cards, choose_companion`: current state
    - `depth`: current search depth
    - `alpha, beta`: alpha–beta bounds
    - `maximizing_player`: True if the 'current' mover is player1, False if player2

    We'll treat 'player1' as the maximizing player, and 'player2' as the minimizing.
    """

    # Base case: or if no moves
    if depth == 0:
        return evaluate_state(player1, player2), None

    # get moves
    if choose_companion:
        possible_moves = get_companion_moves(cards, companion_cards)
        # If no companion moves are possible, effectively pass
        if not possible_moves:
            return evaluate_state(player1, player2), None
    else:
        possible_moves = get_valid_moves(cards)

    if not possible_moves:
        # no moves => evaluate
        return evaluate_state(player1, player2), None

    if maximizing_player:
        best_score = float("-inf")
        best_move = None

        for move in possible_moves:
            # Clone
            new_cards, new_p1, new_p2 = clone_game_state(cards, player1, player2)
            new_companions = copy.deepcopy(companion_cards)

            # Apply
            house_chosen = None
            next_choose_companion = False

            if choose_companion:
                # Minimal usage: just pick the companion, no board changes
                house_chosen = make_companion_move(new_cards, new_companions, move, new_p1)
                # There's a special case if the companion is Melisandre, that yields an extra turn
                # We ignore that to keep code simpler. 
                # Next turn would belong to the other player unless it's Melisandre, etc.
                # Also, there's the real logic with Jaqen, etc. For demonstration, we skip.
                # We'll assume we pass the turn to player2.
                next_player_is_max = False

            else:
                # Normal move for player1
                house_chosen = make_normal_move(new_cards, move, new_p1)
                # If house_chosen is exhausted => next_choose_companion = True
                if house_chosen is not None:
                    count_in_board = sum(1 for c in new_cards if c.get_house() == house_chosen)
                    if count_in_board == 0 and len(new_companions) > 0:
                        next_choose_companion = True

                # Next turn is player2
                next_player_is_max = False

            # Recurse
            score, _ = minimax(
                new_cards, new_p1, new_p2, new_companions,
                next_choose_companion, depth - 1, alpha, beta, next_player_is_max
            )

            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score, best_move

    else:
        # Minimizing player's turn => player2
        best_score = float("inf")
        best_move = None

        for move in possible_moves:
            new_cards, new_p1, new_p2 = clone_game_state(cards, player1, player2)
            new_companions = copy.deepcopy(companion_cards)

            house_chosen = None
            next_choose_companion = False

            if choose_companion:
                house_chosen = make_companion_move(new_cards, new_companions, move, new_p2)
                # Minimal approach
                next_player_is_max = True
            else:
                house_chosen = make_normal_move(new_cards, move, new_p2)
                if house_chosen is not None:
                    count_in_board = sum(1 for c in new_cards if c.get_house() == house_chosen)
                    if count_in_board == 0 and len(new_companions) > 0:
                        next_choose_companion = True
                next_player_is_max = True

            score, _ = minimax(
                new_cards, new_p1, new_p2, new_companions,
                next_choose_companion, depth - 1, alpha, beta, next_player_is_max
            )

            if score < best_score:
                best_score = score
                best_move = move
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score, best_move


# -------------------------------
#        PUBLIC API
# -------------------------------
def get_move(cards, player1, player2, companion_cards, choose_companion):
    """
    Called by the main engine.  We do a shallow depth minimax search (depth=2 or 3).
    Returns a single move:
       - If choose_companion == False, return a board location (int) for the normal move.
       - If choose_companion == True, return a list like [companionName, ...any-other-data...].
    """

    # We'll do a short search (e.g. depth=2).  You can raise this but keep an eye on performance.
    SEARCH_DEPTH = 3

    # For convenience in this script, treat player1 as the maximizing player if
    # the main is currently on "turn=1", i.e. if player1 is about to move. 
    # There's no direct "turn" argument, but we can guess based on the name field:
    #   If player1's agent name is the same as "minimax_agent", we assume it's our turn as maximizing.
    # This is a hack — you can track actual turn from your main if you pass it in.

    # We'll compare the agent's name to guess if it's the maximizing or not.
    # If both are "minimax_agent," then let's assume 'player1' is maximizing and 'player2' is minimizing.
    # (Your environment might do something else. Adjust as needed.)
    p1_is_max = True  # default assumption

    # If needed, you could store who is currently to move in a global, or pass from main. 
    # For now, let's do a trick: if it's "human" vs "minimax_agent", we guess "minimax_agent" is player2 => p1_is_max=False
    if player1.get_agent() == "human" and player2.get_agent() != "human":
        # Then the "minimax_agent" is second => p1_is_max=False
        p1_is_max = False
    # If both are minimax, let's keep the default p1_is_max = True.

    # Run minimax
    _, chosen_move = minimax(
        cards=cards,
        player1=player1,
        player2=player2,
        companion_cards=companion_cards,
        choose_companion=choose_companion,
        depth=SEARCH_DEPTH,
        alpha=float("-inf"),
        beta=float("inf"),
        maximizing_player=p1_is_max
    )

    return chosen_move
