from table import Table
import random
import os
import myparser
from compilator import compilate


data = [
    ['Name', 'Surname', 'Age', 'Kurs'],
    ['Alex', 'Chirkin', 19, 3],
    ['Varya', 'Gospodarikova', 18, 3],
    ['Lesya', 'Lipatova', 18, 1],
    ['Lex', 'Kuduhov', 22, 5],
    ['Alexander', 'Kozhuhov', 20, 3],
    ['Nikolay', 'Paukov', 20, 3],
    ['Vadim', 'Smagin', 18, 2],
    ['Ivan', 'Zaborskih', 20, 2],
    ['Olesya', 'Tranina', 21, 4],
    ['Ruslan', 'Pogorelov', 20, 3]
]
students = Table('students', data)
print(students)

data2 = [
    ['Profession', 'Company', 'Age'],
    ['student', 'university', 22],
    ['developer', 'it company', 20]
]

professions = Table('professions', data2)
print(professions)

data3 = [
    ['Fio', 'Kurs'],
    ['sirota', 1],
    ['minin', 2]
]

lecturers = Table('lecturers', data3)
print(lecturers)


#def comp(arg1, arg2):
#    return bool(random.randint(0, 1))

#students.join(professions, comp)
#print(students)   students.Surname = 'Chirkin' OR p.Age = 20

prog = myparser.parse(
         '''
    SELECT DISTINCT s.Kurs, s
    FROM students s JOIN professions p ON s.Age = p.Age, professions prof
    WHERE s.Kurs = 3 OR Name = 'Lex'
    GROUP BY s.Kurs
    ;
        ''')
#FROM students s1 JOIN professions s2 ON s1.Age  = s2.Age JOIN lecturers l ON l.Kurs = 1 OR l.Kurs = 2 AND s1.Name = 'Ivan'
print(*prog.tree, sep=os.linesep)
print(compilate([students, professions, lecturers], prog))
