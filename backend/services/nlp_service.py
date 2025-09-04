import re
from typing import Dict, List, Optional, Tuple, Any
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from loguru import logger
from config import settings
from models.document import CaseType, UrgencyLevel


class NLPService:
    """NLP service for document classification and entity extraction"""
    
    def __init__(self):
        """Initialize NLP service"""
        try:
            self.nlp = spacy.load(settings.spacy_model)
            logger.info(f"Loaded spaCy model: {settings.spacy_model}")
        except IOError:
            logger.error(f"Could not load spaCy model: {settings.spacy_model}")
            raise
        
        # Legal case type keywords
        self.case_type_keywords = {
            CaseType.CRIMINAL: [
                "criminal", "felony", "misdemeanor", "arrest", "prosecution", "defendant",
                "guilty", "not guilty", "plea", "sentence", "jail", "prison", "probation",
                "parole", "bail", "bond", "indictment", "arraignment", "trial", "jury",
                "verdict", "conviction", "acquittal", "crime", "offense", "violation",
                "murder", "theft", "assault", "robbery", "fraud", "drug", "dui", "dwi"
            ],
            CaseType.CIVIL: [
                "civil", "plaintiff", "defendant", "damages", "liability", "negligence",
                "tort", "contract", "breach", "settlement", "mediation", "arbitration",
                "injunction", "restraining order", "discovery", "deposition", "motion",
                "summary judgment", "trial", "verdict", "appeal", "litigation", "dispute"
            ],
            CaseType.CORPORATE: [
                "corporate", "corporation", "business", "company", "merger", "acquisition",
                "securities", "stock", "shareholder", "board of directors", "compliance",
                "regulatory", "sec", "ipo", "partnership", "llc", "incorporation",
                "bylaws", "articles", "due diligence", "intellectual property", "trademark",
                "patent", "copyright", "trade secret", "licensing", "joint venture"
            ],
            CaseType.FAMILY: [
                "family", "divorce", "custody", "child support", "alimony", "spousal support",
                "adoption", "guardianship", "domestic violence", "restraining order",
                "prenuptial", "postnuptial", "separation", "marital property", "visitation",
                "parenting plan", "mediation", "collaborative divorce", "annulment"
            ],
            CaseType.IMMIGRATION: [
                "immigration", "visa", "green card", "citizenship", "naturalization",
                "deportation", "removal", "asylum", "refugee", "work permit", "h1b",
                "l1", "f1", "tourist visa", "family visa", "uscis", "ice", "cbp",
                "immigration court", "adjustment of status", "consular processing"
            ],
            CaseType.EMPLOYMENT: [
                "employment", "labor", "workplace", "discrimination", "harassment",
                "wrongful termination", "wage", "salary", "overtime", "benefits",
                "workers compensation", "unemployment", "fmla", "ada", "eeoc",
                "union", "collective bargaining", "workplace safety", "osha"
            ],
            CaseType.REAL_ESTATE: [
                "real estate", "property", "deed", "title", "mortgage", "foreclosure",
                "landlord", "tenant", "lease", "rent", "eviction", "zoning", "easement",
                "property tax", "closing", "escrow", "hoa", "condominium", "commercial property"
            ],
            CaseType.TAX: [
                "tax", "irs", "audit", "deduction", "exemption", "penalty", "interest",
                "refund", "return", "income tax", "property tax", "sales tax", "estate tax",
                "gift tax", "tax court", "tax planning", "tax preparation"
            ],
            CaseType.BANKRUPTCY: [
                "bankruptcy", "chapter 7", "chapter 11", "chapter 13", "debtor", "creditor",
                "discharge", "liquidation", "reorganization", "trustee", "automatic stay",
                "proof of claim", "meeting of creditors", "reaffirmation", "exemption"
            ]
        }
        
        # Urgency keywords
        self.urgency_keywords = {
            UrgencyLevel.CRITICAL: [
                "emergency", "urgent", "immediate", "asap", "critical", "deadline today",
                "time sensitive", "expires", "statute of limitations", "appeal deadline",
                "motion due", "hearing tomorrow", "trial next week"
            ],
            UrgencyLevel.HIGH: [
                "high priority", "important", "soon", "deadline", "due date", "time limit",
                "hearing", "trial", "deposition", "discovery deadline", "response required"
            ],
            UrgencyLevel.MEDIUM: [
                "medium priority", "normal", "standard", "regular", "routine", "review",
                "follow up", "status update"
            ],
            UrgencyLevel.LOW: [
                "low priority", "when convenient", "no rush", "informational", "fyi",
                "reference", "archive", "background"
            ]
        }
        
    async def classify_document(self, text: str) -> Dict[str, Any]:
        """
        Classify document and extract entities
        
        Args:
            text: Document text content
            
        Returns:
            Classification results including case type, urgency, entities, etc.
        """
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract entities
            entities = self._extract_entities(doc)
            
            # Classify case type
            case_type, case_confidence = self._classify_case_type(text)
            
            # Determine urgency
            urgency_level, urgency_confidence = self._classify_urgency(text)
            
            # Extract client names (persons and organizations)
            client_names = self._extract_client_names(entities)
            
            # Generate summary
            summary = await self._generate_summary(text)
            
            # Extract key phrases/tags
            tags = self._extract_tags(doc)
            
            return {
                "case_type": case_type,
                "urgency_level": urgency_level,
                "client_names": client_names,
                "entities": entities,
                "summary": summary,
                "tags": tags,
                "confidence_scores": {
                    "case_type": case_confidence,
                    "urgency": urgency_confidence
                }
            }
            
        except Exception as e:
            logger.error(f"Error classifying document: {str(e)}")
            return {
                "case_type": CaseType.OTHER,
                "urgency_level": UrgencyLevel.MEDIUM,
                "client_names": [],
                "entities": {},
                "summary": "",
                "tags": [],
                "confidence_scores": {
                    "case_type": 0.0,
                    "urgency": 0.0
                }
            }
    
    def _extract_entities(self, doc) -> Dict[str, List[str]]:
        """Extract named entities from document"""
        entities = {
            "PERSON": [],
            "ORG": [],
            "GPE": [],  # Geopolitical entities
            "DATE": [],
            "MONEY": [],
            "LAW": [],
            "EVENT": []
        }
        
        for ent in doc.ents:
            if ent.label_ in entities and ent.text.strip():
                entities[ent.label_].append(ent.text.strip())
        
        # Remove duplicates while preserving order
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))
        
        return entities
    
    def _classify_case_type(self, text: str) -> Tuple[CaseType, float]:
        """Classify document case type based on keywords"""
        text_lower = text.lower()
        scores = {}
        
        for case_type, keywords in self.case_type_keywords.items():
            score = 0
            keyword_count = 0
            
            for keyword in keywords:
                count = text_lower.count(keyword.lower())
                if count > 0:
                    score += count
                    keyword_count += 1
            
            # Normalize score by keyword diversity and text length
            if keyword_count > 0:
                diversity_bonus = keyword_count / len(keywords)
                length_penalty = min(1.0, 1000 / len(text))  # Penalty for very short texts
                scores[case_type] = (score * diversity_bonus * length_penalty)
        
        if not scores:
            return CaseType.OTHER, 0.0
        
        # Get best match
        best_case_type = max(scores, key=scores.get)
        best_score = scores[best_case_type]
        
        # Normalize confidence score
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.0
        
        return best_case_type, min(confidence, 1.0)
    
    def _classify_urgency(self, text: str) -> Tuple[UrgencyLevel, float]:
        """Classify document urgency level based on keywords"""
        text_lower = text.lower()
        scores = {}
        
        for urgency_level, keywords in self.urgency_keywords.items():
            score = 0
            for keyword in keywords:
                count = text_lower.count(keyword.lower())
                score += count
            
            if score > 0:
                scores[urgency_level] = score
        
        # Check for date-based urgency
        date_urgency = self._check_date_urgency(text)
        if date_urgency:
            urgency_level, date_score = date_urgency
            scores[urgency_level] = scores.get(urgency_level, 0) + date_score
        
        if not scores:
            return UrgencyLevel.MEDIUM, 0.5
        
        # Get best match
        best_urgency = max(scores, key=scores.get)
        best_score = scores[best_urgency]
        
        # Normalize confidence
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.0
        
        return best_urgency, min(confidence, 1.0)
    
    def _check_date_urgency(self, text: str) -> Optional[Tuple[UrgencyLevel, float]]:
        """Check for date-based urgency indicators"""
        # Look for urgent date patterns
        urgent_patterns = [
            r"due\s+(today|tomorrow|this\s+week)",
            r"expires?\s+(today|tomorrow|this\s+week)",
            r"deadline\s+(today|tomorrow|this\s+week)",
            r"hearing\s+(today|tomorrow|this\s+week)"
        ]
        
        for pattern in urgent_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return UrgencyLevel.CRITICAL, 2.0
        
        return None
    
    def _extract_client_names(self, entities: Dict[str, List[str]]) -> List[str]:
        """Extract potential client names from entities"""
        client_names = []
        
        # Add person names
        client_names.extend(entities.get("PERSON", []))
        
        # Add organizations (potential corporate clients)
        client_names.extend(entities.get("ORG", []))
        
        # Filter out common legal terms that aren't client names
        legal_terms = {
            "court", "judge", "attorney", "lawyer", "counsel", "plaintiff", "defendant",
            "state", "government", "united states", "u.s.", "usa", "district court",
            "supreme court", "appellate court", "superior court"
        }
        
        filtered_names = []
        for name in client_names:
            if name.lower().strip() not in legal_terms and len(name.strip()) > 2:
                filtered_names.append(name.strip())
        
        return list(dict.fromkeys(filtered_names))  # Remove duplicates
    
    async def _generate_summary(self, text: str, max_sentences: int = 3) -> str:
        """Generate a summary of the document"""
        try:
            # Process text
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 20]
            
            if len(sentences) <= max_sentences:
                return " ".join(sentences)
            
            # Simple extractive summarization using TF-IDF
            vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
            
            if len(sentences) < 2:
                return sentences[0] if sentences else ""
            
            # Vectorize sentences
            sentence_vectors = vectorizer.fit_transform(sentences)
            
            # Calculate sentence scores (sum of TF-IDF scores)
            sentence_scores = np.array(sentence_vectors.sum(axis=1)).flatten()
            
            # Get top sentences
            top_indices = sentence_scores.argsort()[-max_sentences:][::-1]
            top_indices.sort()  # Maintain original order
            
            summary_sentences = [sentences[i] for i in top_indices]
            return " ".join(summary_sentences)
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback: return first few sentences
            sentences = text.split('. ')[:max_sentences]
            return '. '.join(sentences) + '.' if sentences else ""
    
    def _extract_tags(self, doc, max_tags: int = 10) -> List[str]:
        """Extract key phrases/tags from document"""
        try:
            tags = []
            
            # Extract noun phrases
            noun_phrases = [chunk.text.lower().strip() 
                          for chunk in doc.noun_chunks 
                          if len(chunk.text.strip()) > 3 and chunk.text.lower().strip() not in STOP_WORDS]
            
            # Extract named entities as tags
            entity_tags = [ent.text.lower().strip() for ent in doc.ents 
                          if len(ent.text.strip()) > 3]
            
            # Combine and filter
            all_tags = noun_phrases + entity_tags
            
            # Remove duplicates and common words
            common_words = {"document", "case", "court", "legal", "law", "attorney", "lawyer"}
            filtered_tags = []
            
            for tag in all_tags:
                if (tag not in common_words and 
                    tag not in filtered_tags and 
                    len(tag.split()) <= 3):  # Limit to 3 words max
                    filtered_tags.append(tag)
            
            return filtered_tags[:max_tags]
            
        except Exception as e:
            logger.error(f"Error extracting tags: {str(e)}")
            return []


# Global NLP service instance
nlp_service = NLPService() 