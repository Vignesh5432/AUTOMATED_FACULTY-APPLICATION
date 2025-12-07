from flask import Flask, render_template
from auth.login import auth_bp
from auth.logout import logout_bp      # ✅ Correct
from faculty.faculty_routes import faculty_bp
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ✅ Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(logout_bp)
app.register_blueprint(faculty_bp)

@app.route("/")
def home():
    return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)
