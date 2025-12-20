from typing import List, Tuple

def run_second_price_auction(bids: List[float]) -> Tuple[int, float]:
    # second price auction. highest bidder wins but pays the second highest bid.
    if not bids:
        return -1, 0.0
        
    if len(bids) == 1:
        return 0, 0.0 
    
    # who won?
    highest_bid = -1.0
    winner_index = -1
    
    for i, bid in enumerate(bids):
        if bid > highest_bid:
            highest_bid = bid
            winner_index = i
            
    # now find the runner up bid
    second_highest_bid = -1.0
    for i, bid in enumerate(bids):
        if i == winner_index:
            continue
        if bid > second_highest_bid:
            second_highest_bid = bid
            
    return winner_index, second_highest_bid
