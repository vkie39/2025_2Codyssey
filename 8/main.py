from fastapi import FastAPI, HTTPException
from model import TodoItem
import csv
import os

app = FastAPI()
FILE_PATH = 'todos.csv'


def read_todos():
    todos = []
    if not os.path.exists(FILE_PATH):
        return todos
    with open(FILE_PATH, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            todos.append(TodoItem(
                id=int(row['id']),
                title=row['title'],
                description=row['description'],
                completed=row['completed'].lower() == 'true'
            ))
    return todos


def write_todos(todos):
    with open(FILE_PATH, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['id', 'title', 'description', 'completed']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for todo in todos:
            writer.writerow(todo.dict())


@app.get('/todos')
def get_todos():
    return read_todos()


@app.get('/todos/{todo_id}')
def get_single_todo(todo_id: int):
    todos = read_todos()
    for todo in todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=404, detail='Todo not found')


@app.post('/todos')
def create_todo(item: TodoItem):
    todos = read_todos()
    todos.append(item)
    write_todos(todos)
    return {'message': 'Todo created', 'todo': item}


@app.put('/todos/{todo_id}')
def update_todo(todo_id: int, item: TodoItem):
    todos = read_todos()
    updated = False
    for i, todo in enumerate(todos):
        if todo.id == todo_id:
            todos[i] = item
            updated = True
            break
    if not updated:
        raise HTTPException(status_code=404, detail='Todo not found')
    write_todos(todos)
    return {'message': 'Todo updated', 'todo': item}


@app.delete('/todos/{todo_id}')
def delete_single_todo(todo_id: int):
    todos = read_todos()
    new_todos = [todo for todo in todos if todo.id != todo_id]
    if len(todos) == len(new_todos):
        raise HTTPException(status_code=404, detail='Todo not found')
    write_todos(new_todos)
    return {'message': 'Todo deleted'}
