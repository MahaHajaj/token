import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    password_hash = Column(String(64))
    
    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)
    
    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)



class Startup(Base):
    __tablename__ = 'startup'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    username = Column(String, ForeignKey('user.username'))
    user = relationship(User)


class Founder(Base):
    __tablename__ = 'founder'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    bio = Column(String(250))
    startup_id = Column(Integer, ForeignKey('startup.id'))
    startup = relationship(Startup)


engine = create_engine('sqlite:///startupwithusers.db')


Base.metadata.create_all(engine)
