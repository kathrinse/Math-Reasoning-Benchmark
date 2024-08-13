from io import StringIO
from contextlib import redirect_stdout
import func_timeout
import math
import numpy as np


def execute_code(code, local_variables=None):
    variables = local_variables.copy() if local_variables else {}

    def _execute(x):
        try:
            f = StringIO()
            with redirect_stdout(f):
                exec(x, variables)
            s = f.getvalue()
            s = s.strip('\n')
            return s
        except Exception:
            return ""
        
    try:
        variables['result'] = func_timeout.func_timeout(5, _execute, args=(code,))
    except func_timeout.FunctionTimedOut:
        variables['result'] = ""
    return variables 



def safe_execute(code_string: str, keys=None):
    def execute(x):
        try:
            exec(x)
            locals_ = locals()
            if keys is None:
                return locals_.get('ans', None)
            else:
                return [locals_.get(k, None) for k in keys]
        except Exception:
            return None
    try:
        ans = func_timeout.func_timeout(5, execute, args=(code_string,))
    except func_timeout.FunctionTimedOut:
        ans = None

    return ans


def eval_expression(code, local_variables=None):
    variables = local_variables.copy() if local_variables else {}
    try:
        result = eval(code, variables)
        return result
    except Exception as e:
        print(e)
    return ""


# The 8-shot prompt by Wei et al. (2022). "Chain-of-thought prompting elicits reasoning in large language models" - for all Math Word Problem except AQuA
def get_8_shot_wei():
    PROMPT = r"""Q: There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?
A: There are 15 trees originally. Then there were 21 trees after some more were planted. So there must have been 21 - 15 = 6. The answer is 6.

Q: If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?
A: There are originally 3 cars. 2 more cars arrive. 3 + 2 = 5.  The answer is 5.

Q: Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?
A: Originally, Leah had 32 chocolates. Her sister had 42. So in total they had 32 + 42 = 74. After eating 35, they had 74 - 35 = 39. The answer is 39.

Q: Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?
A: Jason started with 20 lollipops. Then he had 12 after giving some to Denny. So he gave Denny 20 - 12 = 8. The answer is 8.

Q: Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?
A: Shawn started with 5 toys. If he got 2 toys each from his mom and dad, then that is 4 more toys. 5 + 4 = 9. The answer is 9.

Q: There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?
A: There were originally 9 computers. For each of 4 days, 5 more computers were added. So 5 * 4 = 20 computers were added. 9 + 20 is 29. The answer is 29.

Q: Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?
A: Michael started with 58 golf balls. After losing 23 on tuesday, he had 58 - 23 = 35. After losing 2 more, he had 35 - 2 = 33 golf balls. The answer is 33.

Q: Olivia has \$23. She bought five bagels for \$3 each. How much money does she have left?
A: Olivia had 23 dollars. 5 bagels for 3 dollars each will be 5 x 3 = 15 dollars. So she has 23 - 15 dollars left. 23 - 15 is 8. The answer is 8."""
    NEW_SAMPLE = "\n\nQ: {question}\nA:"
    ANSWER = "A:"
    return PROMPT, NEW_SAMPLE, ANSWER


def get_4_shot_wei_aqua():
    PROMPT = r"""Q: John found that the average of 15 numbers is 40. If 10 is added to each number then the mean of the numbers is?
Answer Choices: (a) 50 (b) 45 (c) 65 (d) 78 (e) 64
A: If 10 is added to each number, then the mean of the numbers also increases by 10. So the new mean would be 50. The answer is (a).

Q: If a / b = 3/4 and 8a + 5b = 22,then find the value of a.
Answer Choices: (a) 1/2 (b) 3/2 (c) 5/2 (d) 4/2 (e) 7/2
A: If a / b = 3/4, then b = 4a / 3. So 8a + 5(4a / 3) = 22. This simplifies to 8a + 20a / 3 = 22, which means 44a / 3 = 22. So a is equal to 3/2. The answer is (b).

Q: A person is traveling at 20 km/hr and reached his destiny in 2.5 hr then find the distance?
Answer Choices: (a) 53 km (b) 55 km (c) 52 km (d) 60 km (e) 50 km
A: The distance that the person traveled would have been 20 km/hr * 2.5 hrs = 50 km. The answer is (e).

Q: How many keystrokes are needed to type the numbers from 1 to 500?
Answer Choices: (a) 1156 (b) 1392 (c) 1480 (d) 1562 (e) 1788
A: There are 9 one-digit numbers from 1 to 9. There are 90 two-digit numbers from 10 to 99. There are 401 three-digit numbers from 100 to 500. 9 + 90(2) + 401(3) = 1392. The answer is (b)."""
    NEW_SAMPLE = "\n\nQ: {question}\nA:"
    ANSWER = "A:"
    return PROMPT, NEW_SAMPLE, ANSWER


# The 8-shot prompt by Gao et al. (2023) "Pal: Program-aided language models." - the same samples as Wei et al., but with code!
def get_8_shot_gao():
    PROMPT = '''
Q: Olivia has $23. She bought five bagels for $3 each. How much money does she have left?

# solution in Python:


def solution():
    """Olivia has $23. She bought five bagels for $3 each. How much money does she have left?"""
    money_initial = 23
    bagels = 5
    bagel_cost = 3
    money_spent = bagels * bagel_cost
    money_left = money_initial - money_spent
    result = money_left
    return result





Q: Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?

# solution in Python:


def solution():
    """Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?"""
    golf_balls_initial = 58
    golf_balls_lost_tuesday = 23
    golf_balls_lost_wednesday = 2
    golf_balls_left = golf_balls_initial - golf_balls_lost_tuesday - golf_balls_lost_wednesday
    result = golf_balls_left
    return result





Q: There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?

# solution in Python:


def solution():
    """There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?"""
    computers_initial = 9
    computers_per_day = 5
    num_days = 4  # 4 days between monday and thursday
    computers_added = computers_per_day * num_days
    computers_total = computers_initial + computers_added
    result = computers_total
    return result





Q: Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?

# solution in Python:


def solution():
    """Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?"""
    toys_initial = 5
    mom_toys = 2
    dad_toys = 2
    total_received = mom_toys + dad_toys
    total_toys = toys_initial + total_received
    result = total_toys
    return result





Q: Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?

# solution in Python:


def solution():
    """Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?"""
    jason_lollipops_initial = 20
    jason_lollipops_after = 12
    denny_lollipops = jason_lollipops_initial - jason_lollipops_after
    result = denny_lollipops
    return result





Q: Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?

# solution in Python:


def solution():
    """Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?"""
    leah_chocolates = 32
    sister_chocolates = 42
    total_chocolates = leah_chocolates + sister_chocolates
    chocolates_eaten = 35
    chocolates_left = total_chocolates - chocolates_eaten
    result = chocolates_left
    return result





Q: If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?

# solution in Python:


def solution():
    """If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?"""
    cars_initial = 3
    cars_arrived = 2
    total_cars = cars_initial + cars_arrived
    result = total_cars
    return result





Q: There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?

# solution in Python:


def solution():
    """There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?"""
    trees_initial = 15
    trees_after = 21
    trees_added = trees_after - trees_initial
    result = trees_added
    return result




'''
    NEW_SAMPLE = "Q: {question}\n\n# solution in Python:\n\n\n"
    ANSWER = "# solution in Python:"
    return PROMPT, NEW_SAMPLE, ANSWER

# The 8-shot prompt by Gao et al. (2023) "Pal: Program-aided language models." - the same samples as Wei et al., but with code! Dense version
def get_8_shot_gao_dense():
    PROMPT = '''
    #Q: Olivia has \$23. She bought five bagels for \$3 each. How much money does she have left?
money_initial = 23
bagels = 5
bagel_cost = 3
money_spent = bagels * bagel_cost
money_left = money_initial - money_spent
print(money_left)

#Q: Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?
golf_balls_initial = 58
golf_balls_lost_tuesday = 23
golf_balls_lost_wednesday = 2
golf_balls_left = golf_balls_initial - golf_balls_lost_tuesday -
golf_balls_lost_wednesday
print(golf_balls_left)

#Q: There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?
computers_initial = 9
computers_per_day = 5
num_days = 4 # 4 days between monday and thursday
computers_added = computers_per_day * num_days
computers_total = computers_initial + computers_added
print(computers_total)

#Q: If there are 3 cars in the parking lot and 2 more cars arrive, how many cars are in the parking lot?
cars_initial = 3
cars_arrived = 2
total_cars = cars_initial + cars_arrived
print(total_cars)

#Q: Leah had 32 chocolates and her sister had 42. If they ate 35, how many pieces do they have left in total?
leah_chocolates = 32
sister_chocolates = 42
total_chocolates = leah_chocolates + sister_chocolates
chocolates_eaten = 35
chocolates_left = total_chocolates - chocolates_eaten
print(chocolates_left)

#Q: Jason had 20 lollipops. He gave Denny some lollipops. Now Jason has 12 lollipops. How many lollipops did Jason give to Denny?
jason_lollipops_initial = 20
jason_lollipops_after = 12
denny_lollipops = jason_lollipops_initial - jason_lollipops_after
print(denny_lollipops)

#Q: There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?
trees_initial = 15
trees_after = 21
trees_added = trees_after - trees_initial
print(trees_added)

#Q: Shawn has five toys. For Christmas, he got two toys each from his mom and dad. How many toys does he have now?
toys_initial = 5
mom_toys = 2
dad_toys = 2
total_received = mom_toys + dad_toys
total_toys = toys_initial + total_received
print(total_toys)

'''
    NEW_SAMPLE = "#Q: {question}\n"
    ANSWER = "?\n"
    return PROMPT, NEW_SAMPLE, ANSWER

# The 4-shot prompt by Lewkowycz et al. (2022) "Solving Quantitative Reasoning Problems with Language Models" (Minerva) - for the MATH dataset
def get_4_shot_lewkowycz():
    PROMPT = r"""Problem:
Find the domain of the expression $\frac{\sqrt{x-2}}{\sqrt{5-x}}$.}

Solution:
The expressions inside each square root must be non-negative. Therefore, $x-2 \ge 0$, so $x\ge2$, and $5 - x \ge 0$, so $x \le 5$. Also, the denominator denominator cannot be equal to zero, so $5-x>0$, which gives $x<5$. Therefore, the domain of the expression is $\boxed{[2,5)}$.
Final Answer: The final answer is $[2,5)$. I hope it is correct.

Problem:
If $\det \mathbf{A} = 2$ and $\det \mathbf{B} = 12,$ then find $\det (\mathbf{A} \mathbf{B}).$

Solution:
We have that $\det (\mathbf{A} \mathbf{B}) = (\det \mathbf{A})(\det \mathbf{B})= (2)(12) = \boxed{24}.$
Final Answer: The final answer is $24$. I hope it is correct.

Problem:
Terrell usually lifts two 20-pound weights 12 times. If he uses two 15-pound weights instead, how many times must Terrell lift them in order to lift the same total weight?                

Solution:
If Terrell lifts two 20-pound weights 12 times, he lifts a total of $2\cdot 12\cdot20=480$ pounds of weight. If he lifts two 15-pound weights instead for $n$ times, he will lift a total of $2\cdot15\cdot n=30n$ pounds of weight. Equating this to 480 pounds, we can solve for $n$:
\begin{align*}         
30n&=480\\
\Rightarrow\qquad n&=480/30=\boxed{16}
\end{align*}
Final Answer: The final answer is $16$. I hope it is correct.

Problem:
If the system of equations

\begin{align*}
6x-4y&=a,\\
6y-9x &=b.
\end{align*}has a solution $(x, y)$ where $x$ and $y$ are both nonzero,
find $\frac{a}{b},$ assuming $b$ is nonzero.

Solution:
If we multiply the first equation by $-\frac{3}{2}$, we obtain 

$$6y-9x=-\frac{3}{2}a.$$Since we also know that $6y-9x=b$, we have 

$$-\frac{3}{2}a=b\Rightarrow\frac{a}{b}=\boxed{-\frac{2}{3}}.$$
Final Answer: The final answer is $-\frac{2}{3}$. I hope it is correct."""
    NEW_SAMPLE = "\n\nProblem: {question}\nSolution:"
    ANSWER = "Solution:"
    return PROMPT, NEW_SAMPLE, ANSWER

# The 4-shot prompt by Gao et al. (2022) "PAL: Program-aided Language Models" - for the AQuA dataset
def get_4_shot_gao_aqua():
    PROMPT = '''Question: How many keystrokes are needed to type the numbers from 1 to 500?
Answer Choices:
(a) 1156
(b) 1392
(c) 1480
(d) 1562
(e) 1788

# solution using Python:

def solution():
    """Question: How many keystrokes are needed to type the numbers from 1 to 500?
    Answer Choices:
    (a) 1156
    (b) 1392
    (c) 1480
    (d) 1562
    (e) 1788
    """
    count_one_digit = 9
    count_two_digit = 90
    count_three_digit = 401
    total_keystrokes = count_one_digit + count_two_digit * 2 + count_three_digit * 3
    result = total_keystrokes
    return result


Question: A person is traveling at 20 km/hr and reached his destiny in 2.5 hr then find the distance?
Answer Choices:
(a) 53 km
(b) 55 km
(c) 52 km
(d) 60 km
(e) 50 km

# solution using Python:

def solution():
    """Question: A person is traveling at 20 km/hr and reached his destiny in 2.5 hr then find the distance?
    Answer Choices:
    (a) 53 km
    (b) 55 km
    (c) 52 km
    (d) 60 km
    (e) 50 km
    """
    speed_km_hr = 20
    time_hr = 2.5
    distance_km = speed_km_hr * time_hr
    result = distance_km
    return result



Question: If a / b = 3/4 and 8a + 5b = 22,then find the value of a.
Answer Choices:
(a) 1/2
(b) 3/2
(c) 5/2
(d) 4/2
(e) 7/2

# solution using Python:

def solution():
    """Question: If a / b = 3/4 and 8a + 5b = 22,then find the value of a.
    Answer Choices:
    (a) 1/2
    (b) 3/2
    (c) 5/2
    (d) 4/2
    (e) 7/2
    """
    a_b = 3/4
    b = 22 / (8 * a_b + 5) 
    a = a_b * b
    result = a
    return result



Question: John found that the average of 15 numbers is 40. If 10 is added to each number then the mean of the numbers is?
Answer Choices:
(a) 50
(b) 45
(c) 65
(d) 78
(e) 64

# solution using Python:

def solution():
    """Question: John found that the average of 15 numbers is 40. If 10 is added to each number then the mean of the numbers is?
    Answer Choices:
    (a) 50
    (b) 45
    (c) 65
    (d) 78
    (e) 64
    """
    mean = 40
    numbers = 15
    added_per_number = 10
    sum = mean * numbers
    new_sum = sum + (added_per_number * numbers)
    new_mean = new_sum / numbers
    result = new_mean
    return result
'''

    NEW_SAMPLE = "\n\nQuestion: {question}\nAnswer Choices: \n{answer_choices}\n\n# solution using Python:"
    ANSWER = "# solution using Python:"
    return PROMPT, NEW_SAMPLE, ANSWER

# The randomly generated 8-shot prompt for the MATH dataset
def get_8_shot_math():
    PROMPT = r"""Question: An isosceles, obtuse triangle has one angle with a degree measure that is 50$\%$ larger than the measure of a right angle. What is the measure, in degrees, of one of the two smallest angles in the triangle? Express your answer as a decimal to the nearest tenth.
Solution: An angle with measure $50\%$ larger than the measure of a right angle has measure $\frac{3}{2}\cdot 90^{\circ}=135^{\circ}$.
Thus the other two angles have a combined measure of $45^{\circ}$.Each one has a measure of
$$\frac{45^{\circ}}{2}=\boxed{22.5^{\circ}}.$$.Final answer: 22.5^{\circ}


Question: Find the value of $x$ for which the matrix \[\begin{pmatrix} 1 + x & 7 \\ 3 - x & 8 \end{pmatrix}\]is not invertible.
Solution: A matrix is not invertible if and only its determinant is 0.  This gives us the equation
\[(1 + x)(8) - (7)(3 - x) = 0.\]Solving, we find $x = \boxed{\frac{13}{15}}.$. Final answer: \frac{13}{15} 


Question: What is the value of $23^2 + 2(23)(2) + 2^2$?
Solution: This is the square of a binomial: $23^2 + 2(23)(2) + 2^2 = (23+2)^2 = 25^2 = \boxed{625}$. Final answer: 625 


Question: The measure of each exterior angle of a regular polygon is $30$ degrees. What is the sum of the measures of the interior angles, in degrees?
Solution: Taking one exterior angle per vertex, the sum of the exterior angles of a polygon is $360^\circ$. If each exterior angle is $30^\circ$, then the polygon has $\frac{360}{30}=12$ sides. The sum of the interior angles of an $n$-sided polygon is $180(n-2)$, so for a polygon with 12 sides, the sum of the interior angles is $180(12-2)=\boxed{1800}$ degrees. Final answer: 1800 


Question: What is the remainder when $11065+11067+11069+11071+11073+11075+11077$ is divided by $14$?
Solution: Since $11065,11067,11069,\ldots,11077$ are $7$ consecutive odd integers, they include exactly one integer from each of the residue classes $1,3,5,7,9,11,13\pmod{14}$ (not necessarily in that order). Therefore, their sum is congruent $\pmod{14}$ to $1+3+5+7+9+11+13=49$. The remainder of this sum $\pmod{14}$ is $\boxed{7}$. Final answer: 7 


Question: Alex bakes a total of $24$ pies, and each pie is apple, blueberry, or cherry. The ratio of apple to blueberry to cherry pies is $1:4:3$. How many cherry pies did Alex bake?
Solution: The $24$ pies are divided into $1+4+3 = 8$ equal parts. Thus, there are $\frac{24}{8} = 3$ pies per part. Since three parts of the pies are cherry, Alex baked $3 \cdot 3 = \boxed{9}$ cherry pies. Final answer: 9 


Question: Triangle $ABC$ with vertices $A(1, -3)$, $B(-2, 0)$ and $C(4, 3)$ is reflected over the $y$-axis to form triangle $A'B'C'$. What is the length of a segment drawn from $A$ to $A'$?
Solution: Reflecting a point over the $y$-axis negates the $x$-coefficient.  So if $A$ is $(1,-3)$, $A'$ will be $(-1, -3)$.  The segment is a horizontal line of length $1+1=\boxed{2}$. Final answer: 2 


Question: What integer is closest to the value of $\sqrt[3]{6^3+8^3}$?
Solution: We have $\sqrt[3]{6^3 + 8^3} = \sqrt[3]{216 + 512} = \sqrt[3]{728}$. To find the integer closest to this, we note that $8^3 = 512$, $9^3= 729$, and $10^3 =1000$, so $\sqrt[3]{728}$ is very close to $\boxed{9}$. Final answer: 9
"""

    NEW_SAMPLE = "\n\nQuestion: {question}\nSolution: "
    ANSWER = 'Solution: '
    return PROMPT, NEW_SAMPLE, ANSWER
