from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id       = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email    = Column(String, unique=True, index=True)
    hashed_pw= Column(String)
    elo      = Column(Integer, default=1200)
    # 対局履歴
    games_white = relationship("Game", back_populates="player_white", foreign_keys="Game.white_id")
    games_black = relationship("Game", back_populates="player_black", foreign_keys="Game.black_id")

class Game(Base):
    __tablename__ = "games"
    id         = Column(String, primary_key=True, index=True)  # UUID
    white_id   = Column(Integer, ForeignKey("users.id"))
    black_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    fen        = Column(String, default="startpos")
    result     = Column(String, nullable=True)  # "1-0","1/2-1/2","0-1"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    time_control = Column(String)  # "5+0","3+2" など
    player_white = relationship("User", foreign_keys=[white_id])
    player_black = relationship("User", foreign_keys=[black_id])
