from sklearn.cluster import KMeans
import cv2
import numpy as np
import requests
import json
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class VisualFeatureExtractor:
    def __init__(self, artifact_path=None):
        if artifact_path is None:
            self.artifact_path = os.path.join(settings.BASE_DIR, 'ml_models', 'artifacts', 'visual_features.json')
        else:
            self.artifact_path = artifact_path

        self.features = self.load_features()

    def load_features(self):
        if os.path.exists(self.artifact_path):
            try:
                with open(self.artifact_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Error loading visual features from %s: %s", self.artifact_path, e)
                return {}
        return {}

    def save_features(self):
        os.makedirs(os.path.dirname(self.artifact_path), exist_ok=True)
        with open(self.artifact_path, 'w') as f:
            json.dump(self.features, f, indent=4)

    def extract_advanced_features(self, movie_id, url):

        if not url:
            return None

        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return None

            img_array = np.array(bytearray(response.content), dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is None:
                return None

            img = cv2.resize(img, (150, 225))

            pixels = img.reshape(-1, 3)
            kmeans = KMeans(n_clusters=3, n_init=10)
            kmeans.fit(pixels)
            colors = kmeans.cluster_centers_.astype(int)

            palette = []
            for c in colors:
                b, g, r = c.tolist()
                palette.append({
                    'r': r, 'g': g, 'b': b,
                    'hex': f'#{r:02x}{g:02x}{b:02x}'
                })

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            avg_sat = np.mean(s)
            avg_val = np.mean(v)

            vibe = "Standard"
            if avg_val < 60: vibe = "Noir/Dark"
            elif avg_sat > 160: vibe = "Neon/Vibrant"
            elif avg_sat < 50 and avg_val > 180: vibe = "Pastel/Soft"
            elif avg_sat < 70: vibe = "Desaturated/Gritty"

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            complexity = cv2.Laplacian(gray, cv2.CV_64F).var()

            style = "Cinematic"
            if complexity < 1000: style = "Minimalist"
            elif complexity > 3500: style = "Action-Packed/Complex"

            feature_data = {
                'palette': palette,
                'dominant_hex': palette[0]['hex'],
                'saturation': float(avg_sat),
                'brightness': float(avg_val),
                'vibe': vibe,
                'complexity': float(complexity),
                'visual_style': style
            }

            self.features[str(movie_id)] = feature_data
            return feature_data

        except Exception as e:
            logger.exception("Error refining movie %s visuals", movie_id)
            return None

    def get_movie_visuals(self, movie_id):
        return self.features.get(str(movie_id))

    def batched_extract(self, movies_queryset, force=False):

        count = 0
        for movie in movies_queryset:
            has_old_data = str(movie.movie_id) in self.features
            is_old_schema = has_old_data and 'palette' not in self.features[str(movie.movie_id)]

            if force or not has_old_data or is_old_schema:
                url = movie.poster_url_external or (movie.poster.url if movie.poster else None)
                if url:
                    self.extract_advanced_features(movie.movie_id, url)
                    count += 1
                    if count % 10 == 0:
                        self.save_features()
        self.save_features()
        return count