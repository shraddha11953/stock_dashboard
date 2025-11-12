from app import db, models

print("Creating all tables...")
models.Base.metadata.create_all(bind=db.engine)
print("Tables created successfully!")
