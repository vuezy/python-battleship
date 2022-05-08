import time
from shipplayer import Human, Computer

def play(*player):
    idx = 0
    player[0].ship_pos()
    player[1].ship_pos()
    while True:
        row, col, drct = player[idx].attack()
        idx += 1
        idx %= 2
        if idx == 0:
            player[idx].get_attacked(row, col, player[1], drct)
            print()
            if player[idx].ship_counter == 0:
                print("YOU LOST!")
                break
        else:
            player[idx].get_attacked(row, col)
            print()
            if player[idx].ship_counter == 0:
                print("YOU WON!")
                break
        player[idx].print_board()
        time.sleep(2)

    time.sleep(1)
    player[0].print_board()
    print()
    player[1].print_board(True)


if __name__ == "__main__":
    print("Hi!")
    time.sleep(1)

    print("This is The BattleShip!")
    time.sleep(1)

    print("Get ready!!!")
    time.sleep(1)

    p1 = Human()
    p2 = Computer()
    play(p1, p2)
