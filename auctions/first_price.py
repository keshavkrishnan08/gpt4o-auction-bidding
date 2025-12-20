from typing import List, Tuple

def run_first_price_auction(bids: List[float]) -> Tuple[int, float]:
    # standard first price. highest bidder wins and pays what they bid.
    if not bids:
        return -1, 0.0
    
    highest_bid = -1.0
    winner_index = -1
    
    # find the highest one. first one found wins ties.
    for i, bid in enumerate(bids):
        if bid > highest_bid:
            highest_bid = bid
            winner_index = i
            
    return winner_index, highest_bid
