#!/usr/bin/env python3
"""
DocuScan Demo Data Generator

This script generates comprehensive demo data for the DocuScan legal document
classification system, including realistic documents, proper classification,
and full Elasticsearch integration.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json
import random
import uuid
from dataclasses import dataclass
import hashlib

# Add the parent directory to sys.path for imports
sys.path.append(str(Path(__file__).parent.parent))

from faker import Faker
from reportlab.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# Import DocuScan components
from backend.config import settings
from backend.models.document import (
    Document, CaseType, UrgencyLevel, DocumentType, DocumentStatus,
    NamedEntity, EntityType, DocumentSummary, ProcessingMetrics
)
from backend.services.elasticsearch_service import ElasticsearchService

# Initialize Faker
fake = Faker()


class DemoDataGenerator:
    """Generates comprehensive demo data for DocuScan."""
    
    def __init__(self):
        self.case_types_data = {
            CaseType.CRIMINAL: {
                "keywords": ["defendant", "charges", "plea", "sentencing", "bail", "evidence", "trial"],
                "titles": ["Criminal Complaint", "Plea Agreement", "Motion to Suppress", "Sentencing Memo"],
                "clients": ["State Attorney", "Public Defender", "District Attorney Office"],
                "urgency_weights": {"critical": 0.15, "high": 0.35, "medium": 0.35, "low": 0.15}
            },
            CaseType.CIVIL: {
                "keywords": ["plaintiff", "defendant", "damages", "settlement", "motion", "discovery"],
                "titles": ["Civil Complaint", "Motion for Summary Judgment", "Settlement Agreement"],
                "clients": ["Private Parties", "Insurance Companies", "Corporations"],
                "urgency_weights": {"critical": 0.05, "high": 0.25, "medium": 0.50, "low": 0.20}
            },
            CaseType.CORPORATE: {
                "keywords": ["corporation", "merger", "acquisition", "shares", "board", "securities"],
                "titles": ["Articles of Incorporation", "Merger Agreement", "Board Resolution"],
                "clients": ["Tech Companies", "Investment Banks", "Law Firms"],
                "urgency_weights": {"critical": 0.20, "high": 0.40, "medium": 0.30, "low": 0.10}
            },
            CaseType.FAMILY: {
                "keywords": ["marriage", "divorce", "custody", "support", "children", "property"],
                "titles": ["Divorce Petition", "Custody Agreement", "Support Order"],
                "clients": ["Family Law Attorneys", "Individuals", "Mediators"],
                "urgency_weights": {"critical": 0.10, "high": 0.30, "medium": 0.40, "low": 0.20}
            },
            CaseType.IMMIGRATION: {
                "keywords": ["visa", "status", "petition", "asylum", "deportation", "naturalization"],
                "titles": ["I-485 Application", "Asylum Petition", "Immigration Appeal"],
                "clients": ["Immigration Law Firms", "Individuals", "Employers"],
                "urgency_weights": {"critical": 0.25, "high": 0.35, "medium": 0.25, "low": 0.15}
            }
        }
        
        self.clients = self._generate_client_list()
        self.law_firms = [
            "Smith & Associates", "Johnson Legal Group", "Williams & Brown LLP",
            "Davis Law Corporation", "Miller Wilson & Co", "Anderson Legal Partners"
        ]
    
    def _generate_client_list(self) -> List[str]:
        """Generate a comprehensive list of client names."""
        clients = []
        
        # Individual clients
        for _ in range(50):
            clients.append(fake.name())
        
        # Corporate clients
        companies = [
            "TechCorp Industries", "Global Dynamics LLC", "Innovative Solutions Inc",
            "Metro Construction Co", "Premier Healthcare Group", "Advanced Manufacturing"
        ]
        clients.extend(companies)
        
        # Government entities
        gov_entities = [
            "State of California", "City of San Francisco", "County of Los Angeles"
        ]
        clients.extend(gov_entities)
        
        return clients
    
    def generate_document(self, case_type: Optional[CaseType] = None) -> Document:
        """Generate a single realistic legal document."""
        
        # Select case type
        if case_type is None:
            case_type = random.choice(list(CaseType))
        
        case_data = self.case_types_data[case_type]
        
        # Generate document content
        content = self._generate_content(case_type, case_data)
        filename = self._generate_filename(case_type)
        
        # Extract information
        client_name = random.choice(case_data["clients"])
        urgency = self._determine_urgency(case_data["urgency_weights"])
        keywords = random.sample(case_data["keywords"], min(5, len(case_data["keywords"])))
        entities = self._generate_entities(content)
        
        # Generate dates
        created_date = fake.date_between(start_date='-1y', end_date='today')
        created_at = fake.date_time_between(
            start_date=created_date,
            end_date=created_date + timedelta(days=1)
        )
        
        deadline_date = None
        if urgency in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]:
            days_ahead = 7 if urgency == UrgencyLevel.CRITICAL else 30
            deadline_date = created_date + timedelta(days=random.randint(1, days_ahead))
        
        # Create document
        document = Document(
            id=uuid.uuid4(),
            filename=filename,
            content=content,
            case_type=case_type,
            urgency_level=urgency,
            document_type=DocumentType.PDF,
            client_name=client_name,
            client_names=[client_name],
            date_created=created_date,
            deadline_date=deadline_date,
            status=DocumentStatus.COMPLETE,
            created_at=created_at,
            updated_at=created_at,
            processed_at=created_at + timedelta(minutes=random.randint(1, 30)),
            entities=entities,
            summary=self._generate_summary(content, keywords),
            tags=self._generate_tags(case_type),
            keywords=keywords,
            file_path=f"demo_documents/{filename}",
            mime_type="application/pdf",
            file_hash=hashlib.md5(content.encode()).hexdigest(),
            language="en",
            metrics=self._generate_metrics(content)
        )
        
        return document
    
    def _generate_content(self, case_type: CaseType, case_data: Dict[str, Any]) -> str:
        """Generate realistic document content."""
        title = random.choice(case_data["titles"])
        
        # Document header
        content = f"CASE NO. {random.randint(2020, 2024)}-{random.randint(1000, 9999)}\n"
        content += f"DATE: {fake.date_this_year().strftime('%B %d, %Y')}\n"
        content += f"ATTORNEY: {random.choice(self.law_firms)}\n"
        content += f"CLIENT: {random.choice(case_data['clients'])}\n\n"
        content += f"{title}\n\n"
        
        # Main content based on case type
        if case_type == CaseType.CRIMINAL:
            content += self._generate_criminal_content()
        elif case_type == CaseType.CIVIL:
            content += self._generate_civil_content()
        elif case_type == CaseType.CORPORATE:
            content += self._generate_corporate_content()
        elif case_type == CaseType.FAMILY:
            content += self._generate_family_content()
        elif case_type == CaseType.IMMIGRATION:
            content += self._generate_immigration_content()
        else:
            content += fake.text(max_nb_chars=2000)
        
        # Add additional paragraphs
        for _ in range(random.randint(2, 4)):
            content += f"\n\n{fake.paragraph(nb_sentences=random.randint(3, 6))}"
        
        # Legal footer
        content += f"\n\nRespectfully submitted,\n\n{fake.name()}\n"
        content += f"Attorney for {random.choice(['Plaintiff', 'Defendant', 'Petitioner'])}\n"
        content += f"State Bar No. {random.randint(100000, 999999)}"
        
        return content
    
    def _generate_criminal_content(self) -> str:
        """Generate criminal law document content."""
        defendant = fake.name()
        crime = random.choice(['burglary', 'assault', 'fraud', 'theft', 'DUI'])
        
        return f"""The defendant {defendant} is hereby charged with {crime} in violation of Penal Code Section {random.randint(100, 999)}.{random.randint(1, 9)}. 

The alleged incident occurred on {fake.date_this_year().strftime('%B %d, %Y')} at approximately {fake.time()} at {fake.address()}. 

Witness {fake.name()} observed the defendant engaging in the alleged criminal conduct. The prosecution seeks appropriate penalties under the law."""
    
    def _generate_civil_content(self) -> str:
        """Generate civil law document content."""
        plaintiff = fake.name()
        defendant = fake.name()
        claim = random.choice(['breach of contract', 'personal injury', 'property damage'])
        
        return f"""Plaintiff {plaintiff} brings this action against Defendant {defendant} for {claim}. 

Plaintiff alleges that on {fake.date_this_year().strftime('%B %d, %Y')}, Defendant's actions caused damages in the amount of ${random.randint(10, 500)},000. 

Plaintiff seeks monetary damages, injunctive relief, and attorney's fees as provided by law."""
    
    def _generate_corporate_content(self) -> str:
        """Generate corporate law document content."""
        company1 = fake.company()
        company2 = fake.company()
        
        return f"""This Agreement provides for the merger of {company1} with and into {company2}. 

The consideration for the merger is ${random.randint(1, 100)} million. The effective date shall be {fake.date_between(start_date='today', end_date='+1y').strftime('%B %d, %Y')}. 

Each share of {company1} will be converted into {random.uniform(0.5, 2.0):.2f} shares of {company2} common stock."""
    
    def _generate_family_content(self) -> str:
        """Generate family law document content."""
        petitioner = fake.first_name()
        respondent = fake.first_name()
        
        return f"""Petitioner {petitioner} and Respondent {respondent} were married on {fake.date_between(start_date='-20y', end_date='-1y').strftime('%B %d, %Y')}. 

Irreconcilable differences have led to the breakdown of the marriage. The parties have {random.randint(0, 3)} minor children. 

Petitioner seeks dissolution of marriage and appropriate orders regarding custody, support, and property division."""
    
    def _generate_immigration_content(self) -> str:
        """Generate immigration law document content."""
        applicant = fake.name()
        country = fake.country()
        
        return f"""Applicant {applicant} seeks adjustment of status to permanent resident of the United States. 

Applicant entered the US on {fake.date_between(start_date='-5y', end_date='-1y').strftime('%B %d, %Y')} with valid visa status. 

Applicant is eligible for adjustment based on family relationship and meets all requirements under immigration law."""
    
    def _generate_filename(self, case_type: CaseType) -> str:
        """Generate realistic filename."""
        case_num = f"{random.randint(2020, 2024)}{random.randint(1000, 9999)}"
        date_str = fake.date_this_year().strftime("%Y%m%d")
        return f"{case_type.value}_{case_num}_{date_str}.pdf"
    
    def _determine_urgency(self, weights: Dict[str, float]) -> UrgencyLevel:
        """Determine urgency level based on weights."""
        levels = [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH, UrgencyLevel.MEDIUM, UrgencyLevel.LOW]
        weights_list = [weights["critical"], weights["high"], weights["medium"], weights["low"]]
        return random.choices(levels, weights=weights_list)[0]
    
    def _generate_entities(self, content: str) -> List[NamedEntity]:
        """Generate named entities for the document."""
        entities = []
        
        # Simple pattern-based entity extraction for demo
        import re
        
        # Extract money amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        for match in re.finditer(money_pattern, content):
            entities.append(NamedEntity(
                text=match.group(),
                label=EntityType.MONEY,
                start=match.start(),
                end=match.end(),
                confidence=0.90
            ))
        
        # Extract dates
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        for match in re.finditer(date_pattern, content):
            entities.append(NamedEntity(
                text=match.group(),
                label=EntityType.DATE,
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))
        
        return entities[:10]  # Limit to 10 entities
    
    def _generate_summary(self, content: str, keywords: List[str]) -> DocumentSummary:
        """Generate document summary."""
        sentences = content.split('.')[:3]
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return DocumentSummary(
            sentences=sentences,
            keywords=keywords[:5],
            topics=keywords[:3],
            confidence=random.uniform(0.7, 0.95)
        )
    
    def _generate_tags(self, case_type: CaseType) -> List[str]:
        """Generate tags for the document."""
        tags = [case_type.value]
        
        # Add some random additional tags
        additional_tags = ["urgent", "confidential", "client-review", "filing", "motion"]
        tags.extend(random.sample(additional_tags, random.randint(1, 3)))
        
        return tags
    
    def _generate_metrics(self, content: str) -> ProcessingMetrics:
        """Generate processing metrics."""
        text_length = len(content)
        
        return ProcessingMetrics(
            ocr_time_seconds=random.uniform(1, 5),
            nlp_time_seconds=random.uniform(2, 8),
            total_time_seconds=random.uniform(5, 15),
            file_size_bytes=random.randint(50000, 200000),
            text_length=text_length,
            confidence_scores={
                'case_type': random.uniform(0.7, 0.95),
                'urgency': random.uniform(0.6, 0.9),
                'entities': random.uniform(0.75, 0.95)
            }
        )


async def main():
    """Main function to generate and index demo data."""
    print("🚀 Starting DocuScan Demo Data Generation...")
    
    # Initialize Elasticsearch service
    elasticsearch_service = ElasticsearchService()
    
    try:
        # Initialize Elasticsearch
        await elasticsearch_service.initialize()
        print("✅ Elasticsearch service initialized")
        
        # Create document generator
        generator = DemoDataGenerator()
        
        # Generate documents
        num_docs = 1000
        print(f"📝 Generating {num_docs} legal documents...")
        
        documents = []
        case_type_counts = {}
        urgency_counts = {}
        
        for i in range(num_docs):
            if i % 100 == 0:
                print(f"Generated {i} documents...")
            
            document = generator.generate_document()
            documents.append(document)
            
            # Track distributions
            case_type = document.case_type
            case_type_counts[case_type] = case_type_counts.get(case_type, 0) + 1
            
            urgency = document.urgency_level
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
        
        print(f"✅ Generated {len(documents)} documents")
        
        # Index documents in Elasticsearch
        print("🔍 Indexing documents in Elasticsearch...")
        
        batch_size = 50
        total_successful = 0
        total_failed = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            successful, failed = await elasticsearch_service.bulk_index_documents(batch)
            total_successful += successful
            total_failed += failed
            
            if (i // batch_size + 1) % 5 == 0:
                print(f"Indexed {i + len(batch)} documents...")
        
        print(f"✅ Indexing completed: {total_successful} successful, {total_failed} failed")
        
        # Wait a moment for Elasticsearch to process
        await asyncio.sleep(2)
        
        # Test dashboard statistics
        print("🔍 Testing dashboard statistics...")
        dashboard_stats = await elasticsearch_service.get_dashboard_statistics()
        print(f"Dashboard shows {dashboard_stats.total_documents} total documents")
        print(f"High priority: {dashboard_stats.high_priority_count}")
        print(f"Critical priority: {dashboard_stats.critical_priority_count}")
        print(f"Active clients: {dashboard_stats.active_clients}")
        
        # Generate statistics report
        print("\n📊 Demo Data Statistics:")
        print(f"Total Documents: {len(documents)}")
        print("\nCase Type Distribution:")
        for case_type, count in sorted(case_type_counts.items()):
            percentage = (count / len(documents)) * 100
            print(f"  {case_type.value}: {count} ({percentage:.1f}%)")
        
        print("\nUrgency Level Distribution:")
        for urgency, count in sorted(urgency_counts.items()):
            percentage = (count / len(documents)) * 100
            print(f"  {urgency.value}: {count} ({percentage:.1f}%)")
        
        # Save metadata
        metadata = {
            "generation_date": datetime.utcnow().isoformat(),
            "total_documents": len(documents),
            "case_type_distribution": {k.value: v for k, v in case_type_counts.items()},
            "urgency_distribution": {k.value: v for k, v in urgency_counts.items()},
            "elasticsearch_indexed": total_successful,
            "elasticsearch_failed": total_failed
        }
        
        # Create demo_documents directory if it doesn't exist
        demo_dir = Path("demo_documents")
        demo_dir.mkdir(exist_ok=True)
        
        metadata_path = demo_dir / "documents_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✅ Demo data generation completed successfully!")
        print(f"📄 Metadata saved to {metadata_path}")
        print(f"🌐 Access the dashboard at http://localhost:3000")
        print(f"📊 {total_successful} documents are now searchable in the system")
        
    except Exception as e:
        print(f"❌ Error during demo data generation: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        # Cleanup
        await elasticsearch_service.close()


if __name__ == "__main__":
    asyncio.run(main()) 