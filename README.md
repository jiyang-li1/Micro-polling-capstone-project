# Micro-polling-capstone-project

### 1 Setup

1 Setup the venv  
```{python}
python -m venv {venv name}
```
2 Activate the venv  
```{bash}
./{venv name}/Scripts/activate
```
3 install all the package in the venv(pip install)  
Flask and sqlalchemy
4 Run .py in venv  
Run db_init.py  
model.py  
main.py  
(Run all the other .py files to make sure you have the test database)

### 2 Need for action

1  ~~Make a admin page to the result~~(finished)  
2  New UI Style  
3  ~~Create a exe easy to update or in the admin panel~~ (finished)
4  ~~More detailed Admin panel~~(finished)
5  admin login function and login page  
6  IP collection for geographic info (?)


### 3 Possible bugs  
~~No way to fetch the data unless manualy enter http://10.44.61.169:5000/poll/1/results~~  (Go to admin to get results)  
Can not verify the admin  
Ugly ui  
Once a choice is deleted the vote record would have no choice but still there and the percentage is not right (check test poll 5)  
Wrong scaling on mobiles  
Original results page not deleted  

### Only zip code 11111,22222,33333,44444,55555 has poll data  
### /admin to get into the admin dashboard (no password)