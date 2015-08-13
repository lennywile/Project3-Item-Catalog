Readme.txt

Lenny Wile
08/13/2015

Project 3 - The Item Catalog

This is a program that allows an authenticated user (via Google+) to add, delete, and edit items by categories using Flask and SQLAlchemy.

Files

application.py - Python code that uses Flask to display the catalog, categories and items.

client_secrets.json - authentication for Google+ application.

database_setup.py - Python code that contains the setup code for the catalog database.

populateDB.py - Python code that performs an initial population of the catalog database.

static\styles.css - CSS styles

templates\additems.html - html code for adding items to the database

templates\catalog.html - html code to display the catalog, categories and items

templates\deleteitem.html - html code that allows for the deletion of an item from the database

templates\edititem.html - html code that allows for the editing of an existing item

templates\header.html - html code that applies to all views

templates\item.html - html code to display a specific item

template\login.html - Google+ login page




How to Run the Code

1. Create the Catalog database.

	a. From the /vagrant/catalog$ prompt, run python database_setup.py
	b. From the /vagrant/catalog$ prompt, run python PopulateDB.py

2. Launch the application.

	a. From the /vagrant/catalog$ prompt, run python application.py
	
3. Launch a browser to access the application.

	a.  http://localhost:8000


