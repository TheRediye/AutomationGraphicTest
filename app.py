import requests
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

app = Flask(__name__)

# Function to fetch match data from API
def fetch_match_data(match_id):
    # Construct the API URL
    url = f"https://api.web.theiconleague.com/website-backend/matches/{match_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        try:
            # Extract necessary data
            team1 = data['home']['name']
            team2 = data['away']['name']
            score1 = str(data['home']['score'])
            score2 = str(data['away']['score'])
            team1_logo_url = "https:" + data['home']['emblem']
            team2_logo_url = "https:" + data['away']['emblem']
            matchday = data['roundNumber']

            return team1, team2, score1, score2, team1_logo_url, team2_logo_url, matchday

        except KeyError as e:
            # Handle missing keys
            print(f"Error extracting data: {e}")
            return None
    else:
        # Handle HTTP errors
        print(f"Failed to fetch data for match ID {match_id}")
        return None

# Function to generate graphic after fetching match data
def generate_graphic(match_id):
    match_data = fetch_match_data(match_id)
    
    if match_data:
        # Unpack match data
        team1, team2, score1, score2, team1_logo_url, team2_logo_url, matchday = match_data

        # Load the base image
        base_img = Image.open("static/images/Base.png")

        # Download and process team logos
        team_logo1_response = requests.get(team1_logo_url)
        team_logo1 = Image.open(BytesIO(team_logo1_response.content)).convert("RGBA").resize((225, 225))

        team_logo2_response = requests.get(team2_logo_url)
        team_logo2 = Image.open(BytesIO(team_logo2_response.content)).convert("RGBA").resize((225, 225))

        # Define positions
        y_center = 1501
        logo1_x_center, logo2_x_center = 150, 900

        # Paste logos onto the base image
        base_img.paste(team_logo1, (logo1_x_center - 225 // 2, y_center - 225 // 2), team_logo1)
        base_img.paste(team_logo2, (logo2_x_center - 225 // 2, y_center - 225 // 2), team_logo2)

        # Draw scores
        draw = ImageDraw.Draw(base_img)
        font_score = ImageFont.truetype("static/fonts/DharmaGothicE-ExBold.ttf", size=235)
        score1_x_center, score2_x_center = 350, 650
        score_y_position = 1375

        draw.text((score1_x_center, score_y_position), score1, font=font_score, fill="black")
        draw.text((score2_x_center, score_y_position), score2, font=font_score, fill="black")

        # Draw matchday text
        font_matchday = ImageFont.truetype("static/fonts/Mehder.otf", size=60)
        matchday_text = f"Matchday {int(matchday):02d}"

        text_bbox = draw.textbbox((0, 0), matchday_text, font=font_matchday)
        text_width = text_bbox[2] - text_bbox[0]

        draw.text(((base_img.width - text_width) // 2, 1060), matchday_text, font=font_matchday, fill="white")

        # Save image to a BytesIO object
        img_io = BytesIO()
        base_img.save(img_io, 'PNG')
        img_io.seek(0)

        # Generate filename
        file_name = f"{team1.replace(' ', '_')}_vs_{team2.replace(' ', '_')}_Matchday{int(matchday):02d}.png"

        return img_io, file_name
    else:
        # Return None if match data couldn't be fetched
        return None, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        match_id = request.form['match_id']
        img_io, file_name = generate_graphic(match_id)
        if img_io:
            # Send the generated image as a file attachment
            return send_file(img_io, mimetype='image/png', as_attachment=True, attachment_filename=file_name)
        else:
            # Render the template with an error message
            error_message = "Failed to generate graphic. Please check the Match ID and try again."
            return render_template('index.html', error=error_message)
    # Render the form template
    return render_template('index.html')

if __name__ == '__main__':
    # Run the app on the specified host and port
    app.run(host='0.0.0.0', port=5000)
