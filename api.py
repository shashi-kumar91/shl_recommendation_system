from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from final_recommend_eng import SHLRecommendationEngine
import os

app = Flask(__name__)
CORS(app)

# Initialize engine
print("🔄 Loading recommendation engine...")
engine = SHLRecommendationEngine()
print("✅ API ready!")

@app.route('/', methods=['GET'])
def home():
    """Root endpoint - API information"""
    return jsonify({
        "message": "SHL Assessment Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "health": {
                "path": "/health",
                "method": "GET",
                "description": "Check API health status"
            },
            "recommend": {
                "path": "/recommend",
                "method": "POST",
                "description": "Get assessment recommendations",
                "body": {
                    "query": "string (required)",
                    "top_k": "integer (optional, default: 10)"
                },
                "example": {
                    "query": "I am hiring for Java developers",
                    "top_k": 10
                }
            }
        },
        "status": "operational"
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "SHL Recommendation API is running",
        "total_assessments": len(engine.df)
    }), 200

@app.route('/recommend', methods=['POST'])
def recommend():
    """Assessment recommendation endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing 'query' field in request body",
                "example": {
                    "query": "I am hiring for Java developers",
                    "top_k": 10
                }
            }), 400
        
        query = data['query']
        top_k = data.get('top_k', 10)
        
        if not query.strip():
            return jsonify({
                "error": "Query cannot be empty"
            }), 400
        
        if not isinstance(top_k, int) or top_k < 1 or top_k > 10:
            return jsonify({
                "error": "top_k must be an integer between 1 and 10"
            }), 400
        
        # Get recommendations
        recommendations = engine.get_recommendations(query, top_k=top_k)
        
        return jsonify({
            "query": query,
            "recommendations": recommendations,
            "count": len(recommendations)
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint with sample query"""
    sample_query = "I am hiring for Java developers who can also collaborate effectively with my business teams."
    recommendations = engine.get_recommendations(sample_query, top_k=5)
    
    return jsonify({
        "test_query": sample_query,
        "recommendations": recommendations,
        "count": len(recommendations),
        "message": "This is a test endpoint. Use POST /recommend for real queries."
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)