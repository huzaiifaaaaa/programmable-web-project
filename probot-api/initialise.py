import os
from flask import Flask
from models import db, UserRole, Model, User

def insert_data():
    if UserRole.query.first() is None:
        print(" * Initializing default database data...")
        customer_role = UserRole(role_name="Customer", description="Standard user")
        
        gpt4 = Model(model_key="gpt-4o")
        llama = Model(model_key="llama-3-70b")
        
        db.session.add_all([customer_role, gpt4, llama])
        db.session.commit() 
        
        if User.query.filter_by(email="john@programmableweb.com").first() is None:
            admin_user = User(
                name="John PW",
                email="john@programmableweb.com",
                password="hashed_password_123",
                user_role=customer_role.role_id,
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f" * Created default user: {admin_user.email}")
            
        print("Default data inserted!")