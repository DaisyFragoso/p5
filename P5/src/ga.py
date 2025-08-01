""" 
    Names: Kailey Herrman & Daisy Fragoso 
    Assignment P5 
"""""
import copy
import heapq
import metrics
import multiprocessing.pool as mpool
import os
import random
import shutil
import time
import math

width = 200
height = 16

options = [
    "-",  # an empty space
    "X",  # a solid wall
    "?",  # a question mark block with a coin
    "M",  # a question mark block with a mushroom
    "B",  # a breakable block
    "o",  # a coin
    "|",  # a pipe segment
    "T",  # a pipe top
    "E",  # an enemy
    #"f",  # a flag, do not generate
    #"v",  # a flagpole, do not generate
    #"m"  # mario's start position, do not generate
]

# The level as a grid of tiles


class Individual_Grid(object):
    __slots__ = ["genome", "_fitness"]

    def __init__(self, genome):
        self.genome = copy.deepcopy(genome)
        self._fitness = None

    # Update this individual's estimate of its fitness.
    # This can be expensive so we do it once and then cache the result.
    def calculate_fitness(self):
        measurements = metrics.metrics(self.to_level())
        # Print out the possible measurements or look at the implementation of metrics.py for other keys:
        # print(measurements.keys())
        # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
        # STUDENT Modify this, and possibly add more metrics.  You can replace this with whatever code you like.
        coefficients = dict(
            meaningfulJumpVariance=0.5,
            negativeSpace=0.6,
            pathPercentage=0.5,
            emptyPercentage=0.6,
            linearity=-0.5,
            solvability=2.0
        )
        self._fitness = sum(map(lambda m: coefficients[m] * measurements[m],
                                coefficients))
        level = self.to_level()
        stair_count = 0
        powerup_positions = [] #to store where all the powerups are
        block_positions = [] #to store where all the regular blocks are
        penalties = 0
        for y in range(height):
            for x in range(width):
                tile = level[y][x]
                if tile in ["?", "M", "o"]:
                    powerup_positions.append((x,y)) #store that this tile is a powerup
                
                powerup_positions.sort() #sort so that we can see if powerups are next to each other
                for i in range(len(powerup_positions) -1):
                    x1, _ = powerup_positions[i] 
                    x2, _ = powerup_positions[i+1]
                    if abs(x1-x2) <= 2:
                        penalties -= 1

                
        #         if tile in ["X", "B"]:
        #             block_positions.append((x,y))
                
                #ground should only have X, -, or |
                if y == height - 1 : 
                    ground_tiles = ["X", "-", "|"]
                    if tile not in ground_tiles: 
                        penalties -=1

                # if tile == "X":
                #     part_of_stairs = (
                #         (x > 0 and y + 1 < height and level[y+1][x-1] == "X") or 
                #         (x+1 < width and y+1 < height and level[y+1][x+1] == "X")
                #     )
                    
                #     if (y < height - 1 ) and ((x+1 < width and x-1 > 0) and (y+1 < height and y-1 > 0) and ((level[y-1][x+1] != "X") or (level[y+1][x-1] != "X"))): #if we are at a height not the ground and not apart of a staircase
                #         penalties -= 1
                #find where the pipes are:
                # if tile == "|":
                #     if (y+)

                

                # if tile == "X": #checking for stairs
                #     if (y+1 < height and level[y+1][x] == "X" and ((x+1 < width and level[y][x+1] == "X") or (x-1 >= 0 and level [y][x-1] == "X"))):
                #         stair_count += 1

                # if stair_count > 6: #penalize if the stairs are taller than 6
                #     penalties -= 2 
            
        self._fitness = self._fitness + penalties         
        return self

    # Return the cached fitness value or calculate it as needed.
    def fitness(self):
        if self._fitness is None:
            self.calculate_fitness()
        return self._fitness

    # Mutate a genome into a new genome.  Note that this is a _genome_, not an individual!
    def mutate(self, genome):
        # STUDENT implement a mutation operator, also consider not mutating this individual
        # STUDENT also consider weighting the different tile types so it's not uniformly random
        # STUDENT consider putting more constraints on this to prevent pipes in the air, etc
        #tile types weights:
        tile_weights = {
            "-" : 40, #An empty space (weighted high because most common tile and dont want the level cluttered)
            "X" : 20, #A solid wall
            "?" : 10, #question mark block with a coin inside
            "M" : 5, #question mark block with a mushroom inside
            "B" : 10, #breakable block (if you are a big Mario)
            "o" : 15, #coin floating in the air
            "|" : 5, #A vertical pipe segment (the position to the right of this will be overwritten with the other side of the pipe automatically)
        }
        mutation_rate = 0.05 #we chose 5% because elitist selection strategy prefers to have small but meaningful mutations
        max_pipe_height = 3
        left = 1
        right = width - 1
        for y in range(height): #we are looping through the grid and deciding which tiles to mutate
            for x in range(left, right):
                #we go line by line, looking through all the x's of each line 
                #choose a random number, if that number is less than .05 then change the tile (5% of the time we mutate)
                #change the genome by using randomnly choosing from the tile options, and adhere to the weights
                if random.random() < mutation_rate: 
                    allowed_tiles = options.copy() #copy so that we can alter the list
                    #constraint: ground can only be made up of 'X' or '-'
                    if y == height - 1 : #ground 
                        allowed_tiles = ['-', 'X']
                    #constraint: no floating pipes 
                    elif (genome[y+1][x] not in ['X', '|']) and (y < height - 1) :
                        if "|" in allowed_tiles:
                            allowed_tiles.remove("|")
                    #constraint: pipes cannot be too tall that mario cant jump over
                    elif(y < height - max_pipe_height):
                        if "|" in allowed_tiles:
                            allowed_tiles.remove("|")
                    #constraint: done put any power up or coin where its unreachable for mario
                    if y+1 < height: #if the tile isnt on the ground, so there is possible to be a block below
                        below = genome[y+1][x]
                        diag_below_left = genome[y+1][x-1] if x-1  >= 0 else None
                        diag_below_right = genome[y+1][x+1] if x+1 < width else None
                        #this will make sure there is a block to jump onto if the power up / coin is high up
                        options_to_jump_from = ['X', '|', 'T', 'B', '?', 'M']
                        if below not in options_to_jump_from and diag_below_left not in options_to_jump_from and diag_below_right not in options_to_jump_from:
                            #no option to jump from
                            remove_tiles = ['?', 'M', 'o']
                            for tile in remove_tiles:
                                if tile in allowed_tiles:
                                    allowed_tiles.remove(tile)
                    

                    weighted_tiles = []
                    for tile in allowed_tiles:
                        if tile in tile_weights:
                            weighted_tiles += [tile] * tile_weights[tile]
                    #this makes a list where each tile is added to the list as many times as their weights
                    #this means that when random chooses a tile, the tile with a higher weight occurs more in the list,
                    #which is a higher percentage of time it will be chosen 

                    genome[y][x] = random.choice(weighted_tiles)

        return genome

    # Create zero or more children from self and other
    def generate_children(self, other):
        # new_genome = copy.deepcopy(self.genome)
        child1_genome = copy.deepcopy(self.genome)
        child2_genome = copy.deepcopy(other.genome)
        # Leaving first and last columns alone...
        # do crossover with other
        left = 1
        right = width - 1
        for y in range(height):
            for x in range(left, right):
                # STUDENT Which one should you take?  Self, or other?  Why?
                # STUDENT consider putting more constraints on this to prevent pipes in the air, etc
                if random.random() < 0.5:
                    child1_genome[y][x] = self.genome[y][x]
                    child2_genome[y][x] = other.genome[y][x]
                else: 
                    child1_genome[y][x] = other.genome[y][x]
                    child2_genome[y][x] = self.genome[y][x]
                # pass
                pass
        # do mutation; note we're returning a one-element tuple here
        # return (Individual_Grid(new_genome),)
        child1_genome = self.mutate(child1_genome)
        child2_genome = self.mutate(child2_genome)
        return (Individual_Grid(child1_genome),Individual_Grid(child2_genome))

    # Turn the genome into a level string (easy for this genome)
    def to_level(self):
        return self.genome

    # These both start with every floor tile filled with Xs
    # STUDENT Feel free to change these
    @classmethod
    def empty_individual(cls):
        g = [["-" for col in range(width)] for row in range(height)]
        g[15][:] = ["X"] * width
        g[14][1] = "m"
        g[7][-2] = "v"
        for col in range(8, 14):
            g[col][-2] = "f"
        for col in range(14, 16):
            g[col][-2] = "X"
        return cls(g)

    @classmethod
    def random_individual(cls):
        # STUDENT consider putting more constraints on this to prevent pipes in the air, etc
        # STUDENT also consider weighting the different tile types so it's not uniformly random
        g = [random.choices(options, k=width) for row in range(height)]
        g[15][:] = ["X"] * width
        g[14][1] = "m"
        g[7][-2] = "v"
        g[8:14][-2] = ["f"] * 6
        g[14:16][-2] = ["X", "X"]
        return cls(g)


def offset_by_upto(val, variance, min=None, max=None):
    val += random.normalvariate(0, variance**0.5)
    if min is not None and val < min:
        val = min
    if max is not None and val > max:
        val = max
    return int(val)


def clip(lo, val, hi):
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val

# Inspired by https://www.researchgate.net/profile/Philippe_Pasquier/publication/220867545_Towards_a_Generic_Framework_for_Automated_Video_Game_Level_Creation/links/0912f510ac2bed57d1000000.pdf


class Individual_DE(object):
    # Calculating the level isn't cheap either so we cache it too.
    __slots__ = ["genome", "_fitness", "_level"]

    # Genome is a heapq of design elements sorted by X, then type, then other parameters
    def __init__(self, genome):
        self.genome = list(genome)
        heapq.heapify(self.genome)
        self._fitness = None
        self._level = None

    # Calculate and cache fitness
    def calculate_fitness(self):
        measurements = metrics.metrics(self.to_level())
        # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
        # STUDENT Add more metrics?
        # STUDENT Improve this with any code you like
        coefficients = dict(
            meaningfulJumpVariance=0.5,
            negativeSpace=0.6,
            pathPercentage=0.5,
            emptyPercentage=0.6,
            linearity=-0.5,
            solvability=2.0
        )
        penalties = 0
        # STUDENT For example, too many stairs are unaesthetic.  Let's penalize that
        if len(list(filter(lambda de: de[1] == "6_stairs", self.genome))) > 5:
            penalties -= 2
        
        #dont put blocks next to stairs 
        stairs = list(filter(lambda de: de[1] == "6_stairs", self.genome))
        blocks = [de for de in self.genome if de[1] == "4_block"] #look through elements to find the blocks
        for block in blocks: #loop through all the blocks
            for stair in stairs: #loop through all the stairs in the level
                if abs(block[0] - stair[0]) <= 1: #if the x coord for block and stair distance is next to each other
                       penalties -= 1

        #dont put a power up next to another power up
        #we check if the element is a qblock, then it checks if it is a power up (de[3] == True), then sorts based on the x coord.
        qblocks = sorted([de for de in self.genome if de[1] == "5q_block" and de[3]], key = lambda de: de[0])
        #now that we have them sorted by their x coords, we can see if two q blocks are next to each other
        for i in range(len(qblocks) -1 ):
            if abs(qblocks[i][0] - qblocks[i+1][0]) <= 2: #distance between current and next q block
                penalities -= 2


        
        # STUDENT If you go for the FI-2POP extra credit, you can put constraint calculation in here too and cache it in a new entry in __slots__.
        self._fitness = sum(map(lambda m: coefficients[m] * measurements[m],
                                coefficients)) + penalties
        return self

    def fitness(self):
        if self._fitness is None:
            self.calculate_fitness()
        return self._fitness
    
    def is_valid_helper(new_de, genome):
        #to prevent two powerups close to each other
        if new_de[1] == "5_qblock" and new_de[3]:
            for de in genome:
                if de[1] == "5_qblock" and de[3] and abs(de[0] - new_de[0]) <= 2:
                    return False
        
        # to prevent blocks next to stairs
        if new_de[1] == "4_block":
            for de in genome:
                if de[1] == "6_stairs" and abs(de[0] - new_de[0]) <= 1:
                    return False
        return True

    def mutate(self, new_genome):
        # STUDENT How does this work?  Explain it in your writeup.
        # STUDENT consider putting more constraints on this, to prevent generating weird things
        if random.random() < 0.1 and len(new_genome) > 0:
            to_change = random.randint(0, len(new_genome) - 1)
            de = new_genome[to_change]
            new_de = de
            x = de[0]
            de_type = de[1]
            choice = random.random()
            if de_type == "4_block":
                y = de[2]
                breakable = de[3]
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                else:
                    breakable = not de[3]
                new_de = (x, de_type, y, breakable)
            elif de_type == "5_qblock":
                y = de[2]
                has_powerup = de[3]  # boolean
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                else:
                    has_powerup = not de[3]
                new_de = (x, de_type, y, has_powerup)
            elif de_type == "3_coin":
                y = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                new_de = (x, de_type, y)
            elif de_type == "7_pipe":
                h = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    h = offset_by_upto(h, 2, min=2, max=height - 4)
                new_de = (x, de_type, h)
            elif de_type == "0_hole":
                w = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    w = offset_by_upto(w, 4, min=1, max=width - 2)
                new_de = (x, de_type, w)
            elif de_type == "6_stairs":
                h = de[2]
                dx = de[3]  # -1 or 1
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    h = offset_by_upto(h, 8, min=1, max=height - 4)
                else:
                    dx = -dx
                new_de = (x, de_type, h, dx)
            elif de_type == "1_platform":
                w = de[2]
                y = de[3]
                madeof = de[4]  # from "?", "X", "B"
                if choice < 0.25:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.5:
                    w = offset_by_upto(w, 8, min=1, max=width - 2)
                elif choice < 0.75:
                    y = offset_by_upto(y, height, min=0, max=height - 1)
                else:
                    madeof = random.choice(["?", "X", "B"])
                new_de = (x, de_type, w, y, madeof)
            elif de_type == "2_enemy":
                pass

            if is_valid_helper(new_de, new_genome):
                new_genome.pop(to_change)
                heapq.heappush(new_genome, new_de)
            # new_genome.pop(to_change)
            # heapq.heappush(new_genome, new_de)
        return new_genome

    def generate_children(self, other):
        # STUDENT How does this work?  Explain it in your writeup.
        pa = random.randint(0, len(self.genome) - 1)
        pb = random.randint(0, len(other.genome) - 1)
        a_part = self.genome[:pa] if len(self.genome) > 0 else []
        b_part = other.genome[pb:] if len(other.genome) > 0 else []
        ga = a_part + b_part
        b_part = other.genome[:pb] if len(other.genome) > 0 else []
        a_part = self.genome[pa:] if len(self.genome) > 0 else []
        gb = b_part + a_part
        # do mutation
        return Individual_DE(self.mutate(ga)), Individual_DE(self.mutate(gb))

    # Apply the DEs to a base level.
    def to_level(self):
        if self._level is None:
            base = Individual_Grid.empty_individual().to_level()
            for de in sorted(self.genome, key=lambda de: (de[1], de[0], de)):
                # de: x, type, ...
                x = de[0]
                de_type = de[1]
                if de_type == "4_block":
                    y = de[2]
                    breakable = de[3]
                    base[y][x] = "B" if breakable else "X"
                elif de_type == "5_qblock":
                    y = de[2]
                    has_powerup = de[3]  # boolean
                    base[y][x] = "M" if has_powerup else "?"
                elif de_type == "3_coin":
                    y = de[2]
                    base[y][x] = "o"
                elif de_type == "7_pipe":
                    h = de[2]
                    base[height - h - 1][x] = "T"
                    for y in range(height - h, height):
                        base[y][x] = "|"
                elif de_type == "0_hole":
                    w = de[2]
                    for x2 in range(w):
                        base[height - 1][clip(1, x + x2, width - 2)] = "-"
                elif de_type == "6_stairs":
                    h = de[2]
                    dx = de[3]  # -1 or 1
                    for x2 in range(1, h + 1):
                        for y in range(x2 if dx == 1 else h - x2):
                            base[clip(0, height - y - 1, height - 1)][clip(1, x + x2, width - 2)] = "X"
                elif de_type == "1_platform":
                    w = de[2]
                    h = de[3]
                    madeof = de[4]  # from "?", "X", "B"
                    for x2 in range(w):
                        base[clip(0, height - h - 1, height - 1)][clip(1, x + x2, width - 2)] = madeof
                elif de_type == "2_enemy":
                    base[height - 2][x] = "E"
            self._level = base
        return self._level

    @classmethod
    def empty_individual(_cls):
        # STUDENT Maybe enhance this
        g = []
        return Individual_DE(g)

    @classmethod
    def random_individual(_cls):
        # STUDENT Maybe enhance this
        elt_count = random.randint(8, 128)
        g = [random.choice([
            (random.randint(1, width - 2), "0_hole", random.randint(1, 8)),
            (random.randint(1, width - 2), "1_platform", random.randint(1, 8), random.randint(0, height - 1), random.choice(["?", "X", "B"])),
            (random.randint(1, width - 2), "2_enemy"),
            (random.randint(1, width - 2), "3_coin", random.randint(0, height - 1)),
            (random.randint(1, width - 2), "4_block", random.randint(0, height - 1), random.choice([True, False])),
            (random.randint(1, width - 2), "5_qblock", random.randint(0, height - 1), random.choice([True, False])),
            (random.randint(1, width - 2), "6_stairs", random.randint(1, height - 4), random.choice([-1, 1])),
            (random.randint(1, width - 2), "7_pipe", random.randint(2, height - 4))
        ]) for i in range(elt_count)]
        return Individual_DE(g)


Individual = Individual_Grid
#Individual = Individual_DE


def generate_successors(population):
    results = []
    # STUDENT Design and implement this
    # Hint: Call generate_children() on some individuals and fill up results.
    def elitist_selection():
        pop_limit = len(population)
        elite_size = max(1, pop_limit // 5) #max ensures that at least 1 elitist is selected, and we truncate so theres no decimal to pick elitists
        #evaluate fitness of individuals in population
        #sort them from most fit to least fit from fitness evaluation
        for individual in population:
            individual.calculate_fitness()

        sorted_population = sorted(population, key = lambda individual: individual.fitness(), reverse = True)
        #now only take the top 20%
        elites = sorted_population[:elite_size]
        offspring = []
        while len(offspring) < pop_limit - elite_size:
                """make sure to change the name of the function once I know the name"""
                parent1 = tournament_selection() #select parent indiv. using selection operator
                parent2 = tournament_selection()
                #might have to change the call in case implemented differently
                #parent1, parent2 = tournament_selection()
                #create offspring by applying crossover to selected parents
                # Defensive check: skip crossover if either genome is empty
                if not getattr(parent1, 'genome', None) or not getattr(parent2, 'genome', None):
                    continue
                children = parent1.generate_children(parent2)
                for child in children:
                    #apply mutation to the offspring
                    mutated_genome = child.mutate(child.genome)
                    mutated_child = Individual(mutated_genome)
                    mutated_child.calculate_fitness() #Evaluate the fitness of the offspring.
                    offspring.append(mutated_child)
                    if len(offspring) >= pop_limit - elite_size:
                        break
                
        #combine the elites + offspring to form new population
        new_population = elites + offspring

        return new_population
               

    def tournament_selection():
        competitors = random.sample(population, 3)
        for individual in competitors:
            individual.calculate_fitness()

        #
        best = competitors[0]
        for c in competitors[1:]:
            if c.fitness() > best.fitness():
                best = c
        return best
        #pass
    

    results = elitist_selection()
    return results


def ga():
    # STUDENT Feel free to play with this parameter
    pop_limit = 480
    # Code to parallelize some computations
    batches = os.cpu_count()
    if pop_limit % batches != 0:
        print("It's ideal if pop_limit divides evenly into " + str(batches) + " batches.")
    batch_size = int(math.ceil(pop_limit / batches))
    with mpool.Pool(processes=os.cpu_count()) as pool:
        init_time = time.time()
        # STUDENT (Optional) change population initialization
        population = [Individual.random_individual() if random.random() < 0.9
                      else Individual.empty_individual()
                      for _g in range(pop_limit)]
        # But leave this line alone; we have to reassign to population because we get a new population that has more cached stuff in it.
        population = pool.map(Individual.calculate_fitness,
                              population,
                              batch_size)
        init_done = time.time()
        print("Created and calculated initial population statistics in:", init_done - init_time, "seconds")
        generation = 0
        start = time.time()
        now = start
        print("Use ctrl-c to terminate this loop manually.")
        try:
            while True:
                now = time.time()
                # Print out statistics
                if generation > 0:
                    best = max(population, key=Individual.fitness)
                    print("Generation:", str(generation))
                    print("Max fitness:", str(best.fitness()))
                    print("Average generation time:", (now - start) / generation)
                    print("Net time:", now - start)
                    with open("levels/last.txt", 'w') as f:
                        for row in best.to_level():
                            f.write("".join(row) + "\n")
                generation += 1
                # STUDENT Determine stopping condition
                stop_condition = False
                if stop_condition:
                    break
                # STUDENT Also consider using FI-2POP as in the Sorenson & Pasquier paper
                gentime = time.time()
                next_population = generate_successors(population)
                gendone = time.time()
                print("Generated successors in:", gendone - gentime, "seconds")
                # Calculate fitness in batches in parallel
                next_population = pool.map(Individual.calculate_fitness,
                                           next_population,
                                           batch_size)
                popdone = time.time()
                print("Calculated fitnesses in:", popdone - gendone, "seconds")
                population = next_population
        except KeyboardInterrupt:
            pass
    return population


if __name__ == "__main__":
    final_gen = sorted(ga(), key=Individual.fitness, reverse=True)
    best = final_gen[0]
    print("Best fitness: " + str(best.fitness()))
    now = time.strftime("%m_%d_%H_%M_%S")
    # STUDENT You can change this if you want to blast out the whole generation, or ten random samples, or...
    for k in range(0, 10):
        with open("levels/" + now + "_" + str(k) + ".txt", 'w') as f:
            for row in final_gen[k].to_level():
                f.write("".join(row) + "\n")
