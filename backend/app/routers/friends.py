from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, database
from typing import List

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/request", response_model=schemas.FriendRequestOut)
def send_friend_request(req: schemas.FriendRequestCreate, db: Session = Depends(database.get_db), current_user=Depends(get_current_user)):
    # 自分から相手への申請を作成
    fr = models.FriendRequest(from_user_id=current_user.id, to_user_id=req.to_user_id)
    db.add(fr); db.commit(); db.refresh(fr)
    return fr

@router.post("/respond", response_model=schemas.FriendRequestOut)
def respond_friend_request(action: schemas.FriendAction, db: Session = Depends(database.get_db), current_user=Depends(get_current_user)):
    fr = db.query(models.FriendRequest).get(action.request_id)
    if not fr or fr.to_user_id != current_user.id:
        raise HTTPException(404, "申請が見つかりません")
    fr.accepted = action.accept
    db.commit(); db.refresh(fr)
    return fr

@router.get("/list", response_model=List[schemas.FriendRequestOut])
def list_friends(db: Session = Depends(database.get_db), current_user=Depends(get_current_user)):
    # 自分が承認したまたは相手が承認した申請を一覧
    qs = db.query(models.FriendRequest).filter(
        ((models.FriendRequest.from_user_id==current_user.id) | 
         (models.FriendRequest.to_user_id==current_user.id)) &
        (models.FriendRequest.accepted==True)
    )
    return qs.all()
