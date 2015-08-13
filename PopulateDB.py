from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
Robo = User(name="Robo Barista", email="tinnyTim@udacity.com",
            picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(Robo)

#Create me
#Lenny = User(name="Lenny Wile", email="gw835y@att.com",
#            picture='https://lh5.googleusercontent.com/-Amn1f8rFHxQ/VZnuN7zwzNI/AAAAAAAAAB0/jZB-hlrao3c/s211-no/trainwreck-380x281.jpg')
#session.add(Lenny)

Soccer = Category(name="Soccer")
session.add(Soccer)

Basketball = Category(name="Basketball")
session.add(Basketball)

Baseball = Category(name="Baseball")
session.add(Baseball)

Frisbee = Category(name="Frisbee")
session.add(Frisbee)

Snowboarding = Category(name="Snowboarding")
session.add(Snowboarding)

RockClimbing = Category(name="Rock Climbing")
session.add(RockClimbing)

Foosball = Category(name="Foosball")
session.add(Foosball)

Skating = Category(name="Skating")
session.add(Skating)

Hockey = Category(name="Hockey")
session.add(Hockey)

Stick = Item(name="Stick", category=Hockey, owner=Robo)
session.add(Stick)

Goggles = Item(name="Goggles", category=Snowboarding, owner=Robo)
session.add(Goggles)

Snowboard = Item(name="Snowboard",
                 category=Snowboarding,
                 owner=Robo,
                 description="Best for any terrain or conditions.")
session.add(Snowboard)

session.commit()
