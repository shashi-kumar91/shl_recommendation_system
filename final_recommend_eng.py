#!/usr/bin/env python3
"""
FIXED Recommendation Engine - URL normalization & better matching
"""
import json
import re
from typing import List, Dict, Any, Set, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import os


class SHLRecommendationEngine:
    def __init__(self, data_file: str = 'preprocessed_assessments.json',
                 train_file: str = 'Train_file.csv'):
        """Initialize with FIXED URL matching."""
        print("🚀 Initializing SHL Recommendation Engine (FIXED)...")
        
        self.df = self._load_data(data_file)
        print(f"✅ Loaded {len(self.df)} individual test solutions")
        
        # Build URL mappings with normalization
        self._build_url_index()
        
        # Load training data with robust URL matching
        self.train_queries = defaultdict(set)
        self.assessment_training_patterns = defaultdict(set)
        
        if train_file and os.path.exists(train_file):
            self._load_training_data(train_file)
        
        # Build TF-IDF index
        print("🔍 Building TF-IDF search index...")
        self.tfidf_matrix, self.vectorizer = self._build_tfidf_index()
        
        print("✅ Engine ready!")
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for robust matching."""
        url = url.strip().lower()
        
        # Extract slug (last meaningful part)
        parts = url.rstrip('/').split('/')
        slug = parts[-1] if parts else ''
        
        # Build normalized format
        return f"https://www.shl.com/solutions/products/product-catalog/view/{slug}/"
    
    def _build_url_index(self):
        """Build normalized URL index for matching."""
        self.url_to_idx = {}
        self.normalized_to_actual = {}
        
        for idx, row in self.df.iterrows():
            actual_url = row['url'].lower()
            normalized_url = self._normalize_url(actual_url)
            
            self.url_to_idx[actual_url] = idx
            self.normalized_to_actual[normalized_url] = actual_url
    
    def _load_data(self, file_path: str) -> pd.DataFrame:
        """Load preprocessed assessments."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        df['test_type'] = df['test_type'].apply(lambda x: x if isinstance(x, list) else [])
        df['description'] = df['description'].fillna(df['name'])
        
        return df
    
    def _load_training_data(self, train_file: str):
        """Load training data with FIXED URL matching."""
        print(f"📚 Loading training data from {train_file}...")
        train_df = pd.read_csv(train_file)
        
        matched_count = 0
        total_count = len(train_df)
        
        for _, row in train_df.iterrows():
            query = row['Query'].lower().strip()
            train_url = row['Assessment_url'].strip()
            
            # Normalize training URL
            normalized = self._normalize_url(train_url)
            
            # Find matching actual URL in our data
            if normalized in self.normalized_to_actual:
                actual_url = self.normalized_to_actual[normalized]
                self.train_queries[query].add(actual_url)
                self.assessment_training_patterns[actual_url].add(query)
                matched_count += 1
        
        print(f"✅ Processed {total_count} training examples")
        print(f"   Matched {matched_count}/{total_count} URLs in catalog ({matched_count/total_count*100:.1f}%)")
        print(f"   Learned patterns for {len(self.train_queries)} unique queries")
        
        if matched_count < total_count * 0.5:
            print(f"   ⚠️  Warning: Only {matched_count/total_count*100:.0f}% of training URLs matched!")
            print(f"   This suggests URL format issues in scraper or preprocessing.")
    
    def _build_tfidf_index(self) -> Tuple[np.ndarray, TfidfVectorizer]:
        """Build TF-IDF index with enhanced features."""
        enriched_texts = []
        
        for _, row in self.df.iterrows():
            parts = []
            
            # Name (10x weight)
            name = row['name']
            parts.extend([name] * 10)
            
            # Extract technologies from name
            name_lower = name.lower()
            tech_terms = re.findall(
                r'\b(java|python|sql|javascript|selenium|html|css|c\+\+|excel|tableau|aws|azure|react|angular|node)\b',
                name_lower
            )
            parts.extend(tech_terms * 20)  # Very high weight
            
            # Leadership/Executive boost
            if any(kw in name_lower for kw in ['leadership', 'executive', 'coo', 'manager', 'opq']):
                parts.extend(['leadership', 'executive', 'senior', 'management', 'strategy'] * 10)
            
            # Banking/Financial boost
            if any(kw in name_lower for kw in ['bank', 'financial', 'admin', 'clerk']):
                parts.extend(['banking', 'financial', 'administrative', 'clerical'] * 8)
            
            # Test types (15x weight - CRITICAL for matching)
            test_types = row.get('test_type', [])
            parts.extend(test_types * 15)
            
            # Map test codes to keywords
            type_keywords = {
                'K': ['technical', 'knowledge', 'skills', 'programming', 'coding', 'development'] * 5,
                'P': ['personality', 'behavioral', 'collaboration', 'communication', 'interpersonal', 'teamwork'] * 5,
                'C': ['cognitive', 'reasoning', 'analytical', 'problem solving', 'numerical', 'verbal'] * 5,
                'A': ['ability', 'aptitude', 'skills'] * 3,
                'D': ['development', '360', 'feedback'] * 3,
                'S': ['simulation', 'practical'] * 3
            }
            
            for tt in test_types:
                if tt in type_keywords:
                    parts.extend(type_keywords[tt])
            
            # Description (3x)
            desc = row.get('description', '')
            parts.extend([desc] * 3)
            
            # Duration
            if pd.notna(row.get('duration')):
                duration = row['duration']
                parts.append(f"duration {duration} minutes")
                if duration <= 30:
                    parts.extend(['quick', 'short'] * 2)
                elif duration <= 45:
                    parts.extend(['standard', 'medium'] * 2)
            
            enriched_texts.append(' '.join(str(p) for p in parts if p))
        
        vectorizer = TfidfVectorizer(
            max_features=15000,
            ngram_range=(1, 3),
            min_df=1,
            max_df=0.85,
            sublinear_tf=True,
            token_pattern=r'\b[a-zA-Z][a-zA-Z+#\.]*\b'
        )
        
        tfidf_matrix = vectorizer.fit_transform(enriched_texts)
        return tfidf_matrix, vectorizer
    
    def _extract_query_features(self, query: str) -> Dict[str, Any]:
        """Extract query features with ENHANCED soft skills detection."""
        query_lower = query.lower()
        
        features = {
            'technologies': [],
            'skills': [],
            'test_categories': set(),
            'duration_max': None,
            'experience_level': None,
            'soft_skills_required': False
        }
        
        # Technology detection
        tech_patterns = {
            'java': r'\bjava\b(?!\s*script)',
            'javascript': r'\bjavascript|java\s*script|js\b',
            'python': r'\bpython\b',
            'sql': r'\bsql\b',
            'selenium': r'\bselenium\b',
            'excel': r'\bexcel\b',
            'html': r'\bhtml\b',
            'css': r'\bcss\b',
        }
        
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, query_lower):
                features['technologies'].append(tech)
        
        # CRITICAL: Soft skills detection
        collaboration_keywords = [
            'collaborate', 'collaboration', 'collaborative',
            'communicate', 'communication', 'interpersonal',
            'team', 'teamwork', 'stakeholder', 'business teams',
            'work with', 'interact with', 'personality', 'behavioral',
            'soft skills', 'people skills'
        ]
        
        if any(kw in query_lower for kw in collaboration_keywords):
            features['test_categories'].add('P')  # Personality
            features['soft_skills_required'] = True
            features['skills'].extend(['collaboration', 'communication'])
        
        # Technical skills
        if any(word in query_lower for word in ['technical', 'coding', 'programming', 'developer', 'engineer']):
            features['test_categories'].add('K')  # Knowledge
        
        # Cognitive
        if any(word in query_lower for word in ['cognitive', 'analytical', 'reasoning', 'analyst']):
            features['test_categories'].add('C')  # Cognitive
        
        # Duration constraint
        duration_match = re.search(r'(\d+)\s*(?:min|minute)', query_lower)
        if duration_match:
            features['duration_max'] = int(duration_match.group(1))
        
        return features
    
    def _calculate_training_boost(self, query: str, url: str, base_score: float) -> float:
        """Apply STRONG training boost."""
        query_lower = query.lower().strip()
        url_lower = url.lower().strip()
        
        # Normalize both
        norm_query_url = self._normalize_url(url_lower)
        
        # Exact query match - MASSIVE boost
        if query_lower in self.train_queries:
            train_urls = self.train_queries[query_lower]
            norm_train_urls = {self._normalize_url(u) for u in train_urls}
            
            if norm_query_url in norm_train_urls:
                return base_score * 1000.0  # Huge boost
        
        # Similar query match
        query_terms = set(query_lower.split())
        best_similarity = 0.0
        
        for train_query, train_urls in self.train_queries.items():
            norm_train_urls = {self._normalize_url(u) for u in train_urls}
            
            if norm_query_url in norm_train_urls:
                train_terms = set(train_query.split())
                if query_terms and train_terms:
                    similarity = len(query_terms & train_terms) / len(query_terms | train_terms)
                    best_similarity = max(best_similarity, similarity)
        
        if best_similarity > 0.3:
            return base_score * (1 + best_similarity * 100)
        
        return base_score
    
    def _balance_by_category(self, results: List[Dict], 
                            required_categories: Set[str],
                            soft_skills_required: bool,
                            top_k: int) -> List[Dict]:
        """Balance recommendations across categories."""
        if len(required_categories) <= 1 and not soft_skills_required:
            return results[:top_k]
        
        # Categorize
        by_category = defaultdict(list)
        
        for result in results:
            test_types = result.get('test_type', [])
            
            if 'K' in test_types:
                by_category['K'].append(result)
            elif 'P' in test_types:
                by_category['P'].append(result)
            elif 'C' in test_types:
                by_category['C'].append(result)
            elif 'A' in test_types:
                by_category['A'].append(result)
            else:
                by_category['Other'].append(result)
        
        balanced = []
        used_urls = set()
        
        # If soft skills required, ensure 2-3 personality tests
        if soft_skills_required and 'P' in required_categories:
            personality_count = min(3, len(by_category['P']), top_k // 3)
            for result in by_category['P'][:personality_count]:
                if result['url'] not in used_urls:
                    balanced.append(result)
                    used_urls.add(result['url'])
        
        # Fill remaining slots
        remaining = top_k - len(balanced)
        slots_per_cat = max(2, remaining // max(1, len(required_categories)))
        
        for cat in required_categories:
            if cat == 'P' and soft_skills_required:
                continue
            
            added = 0
            for result in by_category[cat]:
                if result['url'] not in used_urls and added < slots_per_cat:
                    balanced.append(result)
                    used_urls.add(result['url'])
                    added += 1
        
        # Fill any remaining with top scores
        for result in results:
            if len(balanced) >= top_k:
                break
            if result['url'] not in used_urls:
                balanced.append(result)
                used_urls.add(result['url'])
        
        return balanced[:top_k]
    
    def get_recommendations(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Get recommendations with training boost - ALWAYS returns results."""
        features = self._extract_query_features(query)
        
        # Build enriched query
        query_parts = [query] * 3
        query_parts.extend(features['technologies'] * 10)
        query_parts.extend(features['skills'] * 8)
        
        # Add test category keywords
        if 'P' in features['test_categories']:
            query_parts.extend(['personality', 'behavioral', 'collaboration', 'communication'] * 5)
        if 'K' in features['test_categories']:
            query_parts.extend(['technical', 'knowledge', 'skills', 'programming'] * 5)
        
        query_text = ' '.join(query_parts)
        query_vec = self.vectorizer.transform([query_text])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Apply training boost
        boosted_scores = []
        for idx, score in enumerate(similarities):
            url = self.df.iloc[idx]['url']
            boosted_score = self._calculate_training_boost(query, url, score)
            boosted_scores.append((idx, boosted_score))
        
        # Sort by score
        boosted_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Collect candidates - RELAXED FILTERING
        candidates = []
        for idx, score in boosted_scores[:100]:  # Increased from 50 to 100
            row = self.df.iloc[idx]
            
            # Duration filter - ONLY if specified
            if features['duration_max']:
                duration = row.get('duration')
                if pd.notna(duration) and duration > features['duration_max'] * 1.2:  # Allow 20% buffer
                    continue
            
            candidates.append({
                'name': row['name'],
                'url': row['url'],
                'description': row.get('description', ''),
                'duration': int(row['duration']) if pd.notna(row.get('duration')) else None,
                'adaptive_support': bool(row.get('adaptive_support', False)),
                'remote_support': bool(row.get('remote_support', False)),
                'test_type': row.get('test_type', []),
                'score': score
            })
        
        # Balance if needed
        if len(features['test_categories']) > 1 or features['soft_skills_required']:
            results = self._balance_by_category(
                candidates,
                features['test_categories'],
                features['soft_skills_required'],
                top_k
            )
        else:
            results = candidates[:top_k]
        
        # FALLBACK: If still no results, return top scored assessments regardless
        if len(results) < 5:
            print(f"   ⚠️  Only {len(results)} results after filtering, adding top scored assessments...")
            results = candidates[:max(5, top_k)]
        
        # ENSURE we always return SOMETHING
        if not results and candidates:
            results = candidates[:top_k]
        elif not results:
            # Last resort: return top 10 by pure TF-IDF score
            print(f"   ⚠️  No candidates found, returning top assessments by score...")
            top_indices = similarities.argsort()[-top_k:][::-1]
            for idx in top_indices:
                row = self.df.iloc[idx]
                results.append({
                    'name': row['name'],
                    'url': row['url'],
                    'description': row.get('description', ''),
                    'duration': int(row['duration']) if pd.notna(row.get('duration')) else None,
                    'adaptive_support': bool(row.get('adaptive_support', False)),
                    'remote_support': bool(row.get('remote_support', False)),
                    'test_type': row.get('test_type', []),
                    'score': similarities[idx]
                })
        
        return results[:10]  # Always return exactly 10 (or less if catalog is small)


def main():
    """Test the fixed engine."""
    engine = SHLRecommendationEngine()
    
    test_query = "I am hiring for Java developers who can also collaborate effectively with my business teams."
    
    print(f"\n{'='*80}")
    print(f"Query: {test_query}")
    print(f"{'='*80}\n")
    
    recs = engine.get_recommendations(test_query, top_k=10)
    
    print(f"Recommendations ({len(recs)}):\n")
    for i, rec in enumerate(recs, 1):
        print(f"{i}. {rec['name']}")
        print(f"   Types: {', '.join(rec['test_type'])}")
        print(f"   URL: {rec['url'][-40:]}")
        print()


if __name__ == "__main__":
    main()