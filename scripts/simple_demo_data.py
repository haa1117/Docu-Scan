#!/usr/bin/env python3
"""
Simplified DocuScan Demo Data Generator

This script generates demo data and directly populates Elasticsearch
without depending on complex backend imports.
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from elasticsearch import AsyncElasticsearch
from faker import Faker

# Initialize Faker
fake = Faker()

class SimpleDemoGenerator:
    """Simplified demo data generator."""
    
    def __init__(self):
        self.case_types = ["criminal", "civil", "corporate", "family", "immigration", "employment", "real_estate", "tax", "bankruptcy"]
        self.urgency_levels = ["critical", "high", "medium", "low"]
        self.document_statuses = ["complete", "processing", "pending", "failed"]
        self.clients = self._generate_clients()
        
    def _generate_clients(self) -> List[str]:
        """Generate client names."""
        clients = []
        # Individual clients
        for _ in range(30):
            clients.append(fake.name())
        
        # Corporate clients
        companies = [
            "TechCorp Industries", "Global Dynamics LLC", "Innovative Solutions Inc",
            "Metro Construction Co", "Premier Healthcare Group", "Advanced Manufacturing",
            "City Legal Services", "State Attorney Office", "County Sheriff Department"
        ]
        clients.extend(companies)
        return clients
    
    def generate_document(self) -> Dict[str, Any]:
        """Generate a single document."""
        case_type = random.choice(self.case_types)
        urgency = random.choice(self.urgency_levels)
        client_name = random.choice(self.clients)
        
        # Generate dates
        created_date = fake.date_between(start_date='-1y', end_date='today')
        created_at = fake.date_time_between(
            start_date=created_date,
            end_date=created_date + timedelta(days=1)
        )
        
        # Generate deadline for urgent cases
        deadline_date = None
        if urgency in ["high", "critical"]:
            days_ahead = 7 if urgency == "critical" else 30
            deadline_date = created_date + timedelta(days=random.randint(1, days_ahead))
        
        # Generate content
        content = self._generate_content(case_type)
        
        document = {
            "id": str(uuid.uuid4()),
            "filename": f"{case_type}_{random.randint(1000, 9999)}_{created_date.strftime('%Y%m%d')}.pdf",
            "content": content,
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "case_type": case_type,
            "urgency_level": urgency,
            "document_type": "pdf",
            "client_name": client_name,
            "client_names": [client_name],
            "status": "complete",
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
            "processed_at": (created_at + timedelta(minutes=random.randint(1, 30))).isoformat(),
            "date_created": created_date.isoformat(),
            "deadline_date": deadline_date.isoformat() if deadline_date else None,
            "tags": [case_type, urgency],
            "keywords": self._generate_keywords(case_type),
            "entities": self._generate_entities(content),
            "summary": {
                "sentences": content.split('.')[:2],
                "keywords": self._generate_keywords(case_type)[:5],
                "topics": [case_type],
                "confidence": round(random.uniform(0.7, 0.95), 2)
            },
            "file_path": f"demo_documents/{case_type}_{random.randint(1000, 9999)}.pdf",
            "mime_type": "application/pdf",
            "file_hash": str(uuid.uuid4()).replace('-', ''),
            "language": "en",
            "metrics": {
                "ocr_time_seconds": round(random.uniform(1, 5), 2),
                "nlp_time_seconds": round(random.uniform(2, 8), 2),
                "total_time_seconds": round(random.uniform(5, 15), 2),
                "file_size_bytes": random.randint(50000, 200000),
                "text_length": len(content),
                "confidence_scores": {
                    "case_type": round(random.uniform(0.7, 0.95), 2),
                    "urgency": round(random.uniform(0.6, 0.9), 2),
                    "entities": round(random.uniform(0.75, 0.95), 2)
                }
            }
        }
        
        return document
    
    def _generate_content(self, case_type: str) -> str:
        """Generate case-specific content."""
        templates = {
            "criminal": "Criminal Case involving charges of {charge}. Defendant {defendant} is scheduled for hearing on {date}. Evidence includes {evidence}. Motion filed for {motion}.",
            "civil": "Civil lawsuit between {plaintiff} and {defendant} regarding {matter}. Damages sought: ${amount}. Discovery phase scheduled for {date}. Settlement discussions ongoing.",
            "corporate": "Corporate matter involving {company} and {transaction}. Board resolution required for {action}. Regulatory compliance with {regulation}. Financial impact: ${amount}.",
            "family": "Family law case involving {parties} regarding {matter}. Child custody arrangements for {children}. Support payments of ${amount} monthly. Court date: {date}.",
            "immigration": "Immigration case for {applicant} seeking {status}. Application filed for {visa_type}. Interview scheduled for {date}. Documentation required: {docs}.",
            "employment": "Employment dispute between {employee} and {employer} regarding {issue}. Termination effective {date}. Severance package: ${amount}. EEOC complaint filed.",
            "real_estate": "Real estate transaction for property at {address}. Purchase price: ${amount}. Closing scheduled for {date}. Title issues: {issues}.",
            "tax": "Tax matter involving {taxpayer} and IRS regarding {year} tax return. Amount in dispute: ${amount}. Audit scheduled for {date}. Documentation submitted.",
            "bankruptcy": "Bankruptcy filing under Chapter {chapter} for {debtor}. Total debt: ${amount}. Meeting of creditors on {date}. Assets to be liquidated."
        }
        
        template = templates.get(case_type, "Legal document regarding {matter} scheduled for {date}.")
        
        # Fill template with fake data
        content = template.format(
            charge=random.choice(["theft", "assault", "fraud", "drug possession"]),
            defendant=fake.name(),
            plaintiff=fake.name(),
            date=fake.date_this_year().strftime("%B %d, %Y"),
            evidence=random.choice(["witness testimony", "video footage", "documents", "forensic analysis"]),
            motion=random.choice(["bail reduction", "evidence suppression", "case dismissal"]),
            matter=random.choice(["contract dispute", "personal injury", "property damage", "breach of warranty"]),
            amount=f"{random.randint(10, 500)},{random.randint(100, 999)}",
            company=fake.company(),
            transaction=random.choice(["merger", "acquisition", "joint venture", "licensing agreement"]),
            action=random.choice(["stock issuance", "dividend distribution", "asset purchase"]),
            regulation=random.choice(["SEC compliance", "SOX requirements", "GDPR compliance"]),
            parties=f"{fake.name()} and {fake.name()}",
            children=random.choice(["two minor children", "one child", "three children"]),
            applicant=fake.name(),
            status=random.choice(["permanent residence", "work authorization", "family reunification"]),
            visa_type=random.choice(["H-1B", "Green Card", "K-1 Fiancé", "F-1 Student"]),
            docs=random.choice(["birth certificate", "marriage certificate", "employment records"]),
            employee=fake.name(),
            employer=fake.company(),
            issue=random.choice(["wrongful termination", "discrimination", "wage dispute", "harassment"]),
            address=fake.address().replace('\n', ', '),
            issues=random.choice(["liens", "easements", "boundary disputes", "zoning restrictions"]),
            taxpayer=fake.name(),
            year=random.randint(2019, 2023),
            chapter=random.choice(["7", "11", "13"]),
            debtor=random.choice([fake.name(), fake.company()])
        )
        
        # Add additional paragraphs
        for _ in range(random.randint(2, 4)):
            content += f"\n\n{fake.paragraph(nb_sentences=random.randint(3, 6))}"
        
        content += f"\n\nRespectfully submitted,\n{fake.name()}\nAttorney for Client"
        
        return content
    
    def _generate_keywords(self, case_type: str) -> List[str]:
        """Generate keywords based on case type."""
        keyword_map = {
            "criminal": ["charges", "defendant", "evidence", "trial", "plea", "sentence"],
            "civil": ["plaintiff", "damages", "settlement", "motion", "discovery", "liability"],
            "corporate": ["merger", "acquisition", "compliance", "securities", "board", "shareholders"],
            "family": ["custody", "support", "divorce", "marriage", "children", "property"],
            "immigration": ["visa", "status", "petition", "asylum", "naturalization", "deportation"],
            "employment": ["termination", "discrimination", "wages", "benefits", "harassment", "wrongful"],
            "real_estate": ["property", "title", "closing", "mortgage", "deed", "zoning"],
            "tax": ["IRS", "audit", "deduction", "liability", "refund", "compliance"],
            "bankruptcy": ["debt", "creditors", "liquidation", "reorganization", "discharge", "assets"]
        }
        
        base_keywords = keyword_map.get(case_type, ["legal", "document", "case", "court"])
        return random.sample(base_keywords, min(5, len(base_keywords)))
    
    def _generate_entities(self, content: str) -> List[Dict[str, Any]]:
        """Generate named entities."""
        entities = []
        
        # Simple pattern matching for demo
        import re
        
        # Money amounts
        money_matches = re.finditer(r'\$[\d,]+(?:\.\d{2})?', content)
        for match in money_matches:
            entities.append({
                "text": match.group(),
                "label": "MONEY",
                "start": match.start(),
                "end": match.end(),
                "confidence": round(random.uniform(0.85, 0.95), 2)
            })
        
        # Dates
        date_matches = re.finditer(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', content)
        for match in date_matches:
            entities.append({
                "text": match.group(),
                "label": "DATE",
                "start": match.start(),
                "end": match.end(),
                "confidence": round(random.uniform(0.90, 0.98), 2)
            })
        
        return entities[:10]  # Limit to 10 entities


async def main():
    """Main function to generate and index demo data."""
    print("🚀 Starting Simplified DocuScan Demo Data Generation...")
    
    # Connect to Elasticsearch
    es = AsyncElasticsearch(
        hosts=[{"host": "localhost", "port": 9200}],
        timeout=30,
        max_retries=3,
        retry_on_timeout=True
    )
    
    try:
        # Test connection
        info = await es.info()
        print(f"✅ Connected to Elasticsearch {info['version']['number']}")
        
        # Create index with mapping
        index_name = "docuscan_documents"
        
        # Delete existing index if it exists
        if await es.indices.exists(index=index_name):
            await es.indices.delete(index=index_name)
            print(f"🗑️ Deleted existing index: {index_name}")
        
        # Create new index
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "filename": {"type": "text"},
                    "content": {"type": "text"},
                    "content_preview": {"type": "text"},
                    "case_type": {"type": "keyword"},
                    "urgency_level": {"type": "keyword"},
                    "client_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "status": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "date_created": {"type": "date"},
                    "deadline_date": {"type": "date"},
                    "tags": {"type": "keyword"},
                    "keywords": {"type": "keyword"}
                }
            }
        }
        
        await es.indices.create(index=index_name, body=mapping)
        print(f"✅ Created index: {index_name}")
        
        # Generate documents
        generator = SimpleDemoGenerator()
        documents = []
        num_docs = 1000
        
        print(f"📝 Generating {num_docs} documents...")
        
        for i in range(num_docs):
            if i % 100 == 0:
                print(f"Generated {i} documents...")
            documents.append(generator.generate_document())
        
        print(f"✅ Generated {len(documents)} documents")
        
        # Bulk index documents
        print("🔍 Indexing documents in Elasticsearch...")
        
        actions = []
        for doc in documents:
            actions.append({
                "_index": index_name,
                "_id": doc["id"],
                "_source": doc
            })
        
        # Bulk index in batches
        batch_size = 100
        successful = 0
        failed = 0
        
        for i in range(0, len(actions), batch_size):
            batch = actions[i:i + batch_size]
            
            try:
                response = await es.bulk(body={"index": {}}, operations=batch)
                
                for item in response['items']:
                    if 'index' in item:
                        if item['index']['status'] in [200, 201]:
                            successful += 1
                        else:
                            failed += 1
                
            except Exception as e:
                print(f"❌ Batch indexing error: {e}")
                failed += len(batch)
            
            if (i // batch_size + 1) % 10 == 0:
                print(f"Indexed {i + len(batch)} documents...")
        
        print(f"✅ Indexing completed: {successful} successful, {failed} failed")
        
        # Wait for indexing to complete
        await asyncio.sleep(3)
        
        # Refresh index
        await es.indices.refresh(index=index_name)
        
        # Verify data
        count_result = await es.count(index=index_name)
        total_count = count_result['count']
        print(f"📊 Total documents in index: {total_count}")
        
        # Generate statistics
        case_type_agg = await es.search(
            index=index_name,
            body={
                "size": 0,
                "aggs": {
                    "case_types": {"terms": {"field": "case_type"}},
                    "urgency_levels": {"terms": {"field": "urgency_level"}}
                }
            }
        )
        
        print("\n📊 Document Statistics:")
        print(f"Total Documents: {total_count}")
        
        print("\nCase Type Distribution:")
        for bucket in case_type_agg['aggregations']['case_types']['buckets']:
            print(f"  {bucket['key']}: {bucket['doc_count']}")
        
        print("\nUrgency Level Distribution:")
        for bucket in case_type_agg['aggregations']['urgency_levels']['buckets']:
            print(f"  {bucket['key']}: {bucket['doc_count']}")
        
        print(f"\n✅ Demo data generation completed successfully!")
        print(f"🌐 Access the dashboard at http://localhost:3000")
        print(f"🔍 API available at http://localhost:8000")
        print(f"📊 {total_count} documents are now searchable in the system")
        
    except Exception as e:
        print(f"❌ Error during demo data generation: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(main()) 