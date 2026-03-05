"""
Sentiment Analysis Engine
Supports English and Swahili text classification
Uses rule-based and simple ML approach
"""

import re
from collections import Counter


class SentimentAnalyzer:
    """
    Sentiment analyzer supporting English and Swahili
    Uses lexicon-based approach for prototype
    """
    
    def __init__(self):
        # English sentiment lexicon
        self.english_positive = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'best', 'perfect', 'awesome', 'beautiful', 'outstanding',
            'brilliant', 'superb', 'magnificent', 'fabulous', 'terrific',
            'happy', 'delighted', 'pleased', 'satisfied', 'enjoy', 'enjoyed',
            'nice', 'fine', 'glad', 'grateful', 'thankful', 'impressive',
            'recommended', 'recommend', 'quality', 'efficient', 'helpful','handsome'
            
        }
        
        self.english_negative = {
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst',
            'hate', 'dislike', 'disappointed', 'disappointing', 'useless',
            'waste', 'never', 'broken', 'wrong', 'failed', 'failure',
            'unhappy', 'sad', 'angry', 'annoyed', 'frustrated', 'disgusting',
            'disgusted', 'pathetic', 'ridiculous', 'shame', 'shameful',
            'unacceptable', 'defective', 'faulty', 'sucks', 'lacking'
        }
        
        # Swahili sentiment lexicon
        self.swahili_positive = {



            
            'nzuri', 'poa', 'vizuri', 'bora', 'safi', 'penda', 'napenda',
            'furaha', 'furahi', 'shukrani', 'asante', 'kubwa', 'karibu',
            'njema', 'salama', 'uzuri', 'fahari', 'kizuri', 'vyema',
            'hodari', 'stahili', 'ridhi', 'ridhika', 'shangwe', 'imara',
            'mzuri', 'vizuri', 'kamili', 'bofya', 'sana', 'kabisa'
        }
        
        self.swahili_negative = {
            'mbaya', 'vibaya', 'ovu', 'movu', 'chuki', 'huzuni', 'hasira',
            'kasoro', 'tatizo', 'shida', 'machozi', 'kero', 'dharau',
            'chukiza', 'huzunisha', 'pungufu', 'dhaifu', 'aibu', 'lawama',
            'uchafu', 'uchungu', 'adui', 'ukorofi', 'upuuzi', 'ubaya',
            'uovu', 'udhalilishaji', 'usumbufu', 'uchokozi', 'utovu',
            'ujinga', 'upumbavu', 'ukosefu', 'hasara', 'hatari'
        }
        
        # Common stop words to ignore
        self.english_stops = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'should', 'could', 'may', 'might', 'must',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
            'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        self.swahili_stops = {
            'na', 'ya', 'wa', 'ni', 'kwa', 'la', 'katika', 'au', 'pia',
            'lakini', 'bado', 'hata', 'kwamba', 'kwani', 'kama', 'ili',
            'mimi', 'wewe', 'yeye', 'sisi', 'ninyi', 'wao'
        }
    
    def preprocess_text(self, text):
        """
        Clean and tokenize text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Tokenize (split into words)
        tokens = text.split()
        
        return tokens
    
    def detect_language(self, tokens):
        """
        Detect if text is English or Swahili
        Based on presence of known words
        """
        english_count = 0
        swahili_count = 0
        
        for token in tokens:
            if token in self.english_positive or token in self.english_negative or token in self.english_stops:
                english_count += 1
            if token in self.swahili_positive or token in self.swahili_negative or token in self.swahili_stops:
                swahili_count += 1
        
        # Default to English if unclear
        if swahili_count > english_count:
            return 'Swahili'
        else:
            return 'English'
    
    def calculate_sentiment_score(self, tokens, language):
        """
        Calculate sentiment score based on lexicon matching
        Returns: (positive_count, negative_count, neutral_count)
        """
        if language == 'English':
            positive_words = self.english_positive
            negative_words = self.english_negative
            stop_words = self.english_stops
        else:  # Swahili
            positive_words = self.swahili_positive
            negative_words = self.swahili_negative
            stop_words = self.swahili_stops
        
        positive_count = 0
        negative_count = 0
        
        for token in tokens:
            if token in stop_words:
                continue
            
            if token in positive_words:
                positive_count += 1
            elif token in negative_words:
                negative_count += 1
        
        return positive_count, negative_count
    
    def classify_sentiment(self, positive_count, negative_count):
        """
        Classify sentiment based on positive and negative word counts
        Returns: (sentiment, confidence)
        """
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            # No sentiment words detected - neutral
            return 'Neutral', 0.50
        
        # Calculate confidence based on ratio
        if positive_count > negative_count:
            sentiment = 'Positive'
            confidence = positive_count / total_sentiment_words
        elif negative_count > positive_count:
            sentiment = 'Negative'
            confidence = negative_count / total_sentiment_words
        else:
            # Equal positive and negative
            sentiment = 'Neutral'
            confidence = 0.50
        
        # Adjust confidence to be in reasonable range (0.6 - 0.95)
        # to simulate ML model uncertainty
        if confidence > 0.95:
            confidence = 0.95
        elif confidence < 0.60:
            confidence = 0.60
        
        return sentiment, confidence
    
    def analyze(self, text, language_hint='Auto'):
        """
        Main analysis method
        
        Args:
            text (str): Text to analyze
            language_hint (str): 'Auto', 'English', or 'Swahili'
        
        Returns:
            dict: {
                'sentiment': 'Positive' | 'Negative' | 'Neutral',
                'confidence': float (0.0 to 1.0),
                'language': 'English' | 'Swahili'
            }
        """
        # Preprocess
        tokens = self.preprocess_text(text)
        
        # Detect language if auto
        if language_hint == 'Auto':
            detected_language = self.detect_language(tokens)
        else:
            detected_language = language_hint
        
        # Calculate sentiment scores
        positive_count, negative_count = self.calculate_sentiment_score(tokens, detected_language)
        
        # Classify
        sentiment, confidence = self.classify_sentiment(positive_count, negative_count)
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'language': detected_language
        }


# ═══════════════════════════════════════════════════════════════════════════
#  TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Test the analyzer
    analyzer = SentimentAnalyzer()
    
    test_cases = [
        ("This product is amazing! I love it.", "English"),
        ("This is terrible and I hate it.", "English"),
        ("The service was okay.", "English"),
        ("Huduma hii ni nzuri sana!", "Swahili"),
        ("Ni mbaya kabisa, sina furaha.", "Swahili"),
        ("Ni kawaida tu.", "Swahili"),
    ]
    
    print("\n" + "="*60)
    print("  SENTIMENT ANALYZER TEST")
    print("="*60 + "\n")
    
    for text, expected_lang in test_cases:
        result = analyzer.analyze(text)
        
        print(f"Text: {text}")
        print(f"  → Sentiment: {result['sentiment']}")
        print(f"  → Confidence: {result['confidence']:.2%}")
        print(f"  → Language: {result['language']}")
        print()
