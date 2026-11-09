"""Create the views. Run: python -m scripts.run_sql"""
from mandi import engine

engine.run_sql_file("sql/views.sql")
print("views created")
