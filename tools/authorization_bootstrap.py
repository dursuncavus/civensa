"""Offline, trusted-operator assignment bootstrap. No HTTP/UI administration surface."""
import argparse
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db import SessionLocal
from app.models import User
from app.authorization_service import assign_membership, deactivate_membership, assign_final_authority


def main():
    if os.getenv('CIVENSA_AUTH_BOOTSTRAP') != '1':
        raise SystemExit('Offline bootstrap requires CIVENSA_AUTH_BOOTSTRAP=1 and a formally authorized local operator.')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operator-user-id',type=int,required=True)
    parser.add_argument('--basis',required=True)
    commands=parser.add_subparsers(dest='operation',required=True)
    member=commands.add_parser('assign-member')
    member.add_argument('--organization-id',type=int,required=True)
    member.add_argument('--department-id',type=int,required=True)
    member.add_argument('--user-id',type=int,required=True)
    member.add_argument('--role',choices=['department_editor','department_director'],required=True)
    member.add_argument('--slot',type=int,choices=[1,2,3],required=True)
    deactivate=commands.add_parser('deactivate-member')
    deactivate.add_argument('--membership-id',type=int,required=True)
    final=commands.add_parser('assign-final')
    final.add_argument('--organization-id',type=int,required=True)
    final.add_argument('--user-id',type=int,required=True)
    args=parser.parse_args()
    with SessionLocal.begin() as db:
        actor=db.get(User,args.operator_user_id)
        if args.operation=='assign-member':
            row=assign_membership(db,actor,args.organization_id,args.department_id,args.user_id,args.role,args.slot,args.basis)
        elif args.operation=='deactivate-member':
            deactivate_membership(db,actor,args.membership_id,args.basis);row=None
        else:
            row=assign_final_authority(db,actor,args.organization_id,args.user_id,args.basis)
        print('Assignment recorded:',row.id if row else args.membership_id)


if __name__=='__main__':
    main()
