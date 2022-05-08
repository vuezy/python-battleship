import re
import time
import random

class PosError(Exception):
    pass


class Board:
    def __init__(self):
        self.board = [[" " for _ in range(8)] for _ in range(8)]

    def __str__(self):
        str_repr = "  "
        for i in range(8):
            str_repr += "   " + str(i + 1)

        str_repr += "\n"
        for i in range(36):
            str_repr += "-"
        str_repr += "\n"

        for i in range(8):
            str_repr += str(i + 1)
            str_repr += "  | "
            str_repr += " | ".join(self.board[i])
            str_repr += " |\n"

        for i in range(36):
            str_repr += "-"
        str_repr += "\n"

        return str_repr


class Player:
    def __init__(self):
        self.ship_counter = 5
        self.ship = []
        self.attacked_square = []
        self.b = Board()

    @staticmethod
    def check_pos(row, col, drct, size):
        if drct == "L" and col - size + 1 < 0:
            return False
        if drct == "R" and col + size - 1 > 7:
            return False
        if drct == "U" and row - size + 1 < 0:
            return False
        if drct == "D" and row + size - 1 > 7:
            return False
        return True

    def place_ship_on_board(self, row, col, drct, size):
        self.ship.append([])
        num = len(self.ship) - 1
        for i in range(size):
            if drct == "L":
                self.b.board[row][col - i] = "O"
                self.ship[num].append([row, col - i])
            if drct == "R":
                self.b.board[row][col + i] = "O"
                self.ship[num].append([row, col + i])
            if drct == "U":
                self.b.board[row - i][col] = "O"
                self.ship[num].append([row - i, col])
            if drct == "D":
                self.b.board[row + i][col] = "O"
                self.ship[num].append([row + i, col])
        self.ship[num].append(size)

    def valid_pos(self, row, col, mode="NML", drct=None, size=None):
        if row < 0 or row > 7 or col < 0 or col > 7:
            return False
        if mode == "ATK" and [row, col] in self.attacked_square:
            return False
        if mode == "SHP":
            for i in range(size):
                if drct == "L" and self.b.board[row][col - i] == "O":
                    return False
                if drct == "R" and self.b.board[row][col + i] == "O":
                    return False
                if drct == "U" and self.b.board[row - i][col] == "O":
                    return False
                if drct == "D" and self.b.board[row + i][col] == "O":
                    return False
        return True

    def attacked_ship(self, row, col, comp, drct):
        for part in self.ship:
            if [row, col] in part:
                part.remove([row, col])
                if comp:
                    comp.previous_target[0] = row
                    comp.previous_target[1] = col
                    comp.previous_target[2] = drct
                    comp.add_target(row, col)
                if len(part) == 1:
                    self.ship_counter -= 1
                    if comp:
                        comp.clean_target(row, col, drct, part[0])
                    return True
                break

        return False

    def get_attacked(self, row, col, comp=None, drct=None):
        if self.b.board[row][col] == "O":
            self.b.board[row][col] = "X"
            if self.attacked_ship(row, col, comp, drct):
                time.sleep(1)
                print(f"{self.whose} ship has been destroyed!")
        else:
            self.b.board[row][col] = "*"
            if comp:
                still_possible = False
                for target in comp.preferable_target:
                    if comp.force_target(*target):
                        still_possible = True
                        break
                if not still_possible:
                    comp.stop_force_target()


class Human(Player):
    def __init__(self):
        super().__init__()
        self.whose = "Your"

    def print_board(self):
        print("Your board:")
        print(self.b)

    def ship_pos(self):
        ship_size = [5, 5, 4, 4, 3]
        direction = ["L", "R", "U", "D"]
        self.print_board()
        i = 0
        while i < 5:
            try:
                print(f"Set your {ship_size[i]}-block ship!")
                print("Direction: L for left, R for right, U for up, D for down")
                pos = re.sub("[\s*]", "", input("Format: row, col, direction\n"))
                pos = re.split(",", pos)

                pos[0] = int(pos[0]) - 1
                pos[1] = int(pos[1]) - 1
                if not self.check_pos(*pos, ship_size[i]) or not self.valid_pos(pos[0], pos[1], "SHP", pos[2], ship_size[i]):
                    raise PosError
                if pos[2] not in direction:
                    raise ValueError

                self.place_ship_on_board(*pos, ship_size[i])
                self.print_board()
                i += 1

            except ValueError:
                print("Please follow the format! (row, col, direction)")
                print('"row" and "col" must be a number from 1 to 8!', end="\n\n")
            except PosError:
                print("Invalid position! Please try again!")
                print('"row" and "col" must be a number from 1 to 8!', end="\n\n")
            time.sleep(1)

    def attack(self):
        while True:
            try:
                pos = re.split("[,\s*]", input("Please type the square you want to attack: (Format: row, col)\n"))
                pos[0] = int(pos[0]) - 1
                pos[1] = int(pos[-1]) - 1
                if not self.valid_pos(*pos, "ATK"):
                    raise PosError
                break
            except ValueError:
                print('"row" and "col" must be a number from 1 to 8!', end="\n\n")
            except PosError:
                print("Invalid position! Please try again!")
                print('"row" and "col" must be a number from 1 to 8!', end="\n\n")
            time.sleep(1)

        self.attacked_square.append([pos[0], pos[1]])
        print(f"You launch an attack to square {pos[0] + 1},{pos[1] + 1}!")
        return pos[0], pos[1], None


class Computer(Player):
    # Computer will target a random square at first
    # If the square contains a part of a ship, Computer will target all squares around that square
    def __init__(self):
        super().__init__()
        self.whose = "Enemy's"
        self.preferable_target = []
        self.target_possibility = [[0 for _ in range(8)] for _ in range(8)]
        self.previous_target = [None, None, None]

    def print_board(self, final=False):
        print("Enemy's board:")
        if final:
            print(self.b)
            return None
        str_repr = str(self.b)
        str_repr = str_repr.replace("O", " ")
        print(str_repr)

    def ship_pos(self):
        ship_size = [5, 5, 4, 4, 3]
        for size in ship_size:
            while True:
                row = random.randint(0, 7)
                col = random.randint(0, 7)
                drct = random.choice(["U", "D", "R", "L"])
                if self.check_pos(row, col, drct, size) and self.valid_pos(row, col, "SHP", drct, size):
                    self.place_ship_on_board(row, col, drct, size)
                    break

    def force_target(self, row, col, drct):
        if not self.previous_target[2]:
            return True
        if (self.previous_target[2] == "L" or self.previous_target[2] == "R") and (drct == "L" or drct == "R"):
            if self.previous_target[0] == row:
                return True
        elif (self.previous_target[2] == "U" or self.previous_target[2] == "D") and (drct == "U" or drct == "D"):
            if self.previous_target[1] == col:
                return True
        return False

    def stop_force_target(self):
        self.previous_target[0] = None
        self.previous_target[1] = None
        self.previous_target[2] = None

    def attack(self):
        drct = None
        while len(self.preferable_target) == 0:
            row = random.randint(0, 7)
            col = random.randint(0, 7)
            if self.valid_pos(row, col, "ATK"):
                break
        if len(self.preferable_target) > 0:
            while True:
                row, col, drct = random.choice(self.preferable_target)
                if self.force_target(row, col, drct):
                    break
            self.preferable_target.remove([row, col, drct])
            self.target_possibility[row][col] = 0

        self.attacked_square.append([row, col])
        print(f"The enemy launches an attack to square {row + 1},{col + 1}!")
        return row, col, drct

    def add_target(self, row, col):
        possible_target = [[0, -1, "L"], [0, 1, "R"], [-1, 0, "U"], [1, 0, "D"]]
        for target in possible_target:
            if self.valid_pos(row + target[0], col + target[1], "ATK"):
                self.target_possibility[row + target[0]][col + target[1]] += 1
                if self.target_possibility[row + target[0]][col + target[1]] == 1:
                    self.preferable_target.append([row + target[0], col + target[1], target[2]])

    def clean_target(self, row, col, drct, size):
        self.stop_force_target()
        possible_edge = [["L", row, col + size - 1], ["R", row, col - size + 1], ["U", row + size - 1, col], ["D", row - size + 1, col]]
        possible_target = [[0, -1, "L"], [0, 1, "R"], [-1, 0, "U"], [1, 0, "D"]]
        for edge in possible_edge:
            if drct == edge[0]:
                for r in range(min(row, edge[1]), max(row, edge[1]) + 1):
                    for c in range(min(col, edge[2]), max(col, edge[2]) + 1):
                        for target in possible_target:
                            target[0] += r
                            target[1] += c
                            if target in self.preferable_target:
                                self.target_possibility[target[0]][target[1]] -= 1
                                if self.target_possibility[target[0]][target[1]] == 0:
                                    self.preferable_target.remove(target)
                            target[0] -= r
                            target[1] -= c
