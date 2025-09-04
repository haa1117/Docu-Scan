#!/usr/bin/env python3
"""
Quick DocuScan Demo Data Population Script
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, date, timedelta
from elasticsearch import AsyncElasticsearch
from faker import Faker

fake = Faker()

async def populate_elasticsearch():
    """Populate Elasticsearch with demo legal documents."""
    print("🚀 Starting DocuScan Demo Data Population...")
    
    # Connect to Elasticsearch
    es = AsyncElasticsearch("http://localhost:9200")
    
    try:
        # Test connection
        info = await es.info()
        print(f"✅ Connected to Elasticsearch {info['version']['number']}")
        
        index_name = "docuscan_documents"
        
        # Delete and recreate index
        if await es.indices.exists(index=index_name):
            await es.indices.delete(index=index_name)
            print(f"🗑️ Deleted existing index")
        
        # Create index with simple mapping
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "filename": {"type": "text"},
                    "content": {"type": "text"},
                    "case_type": {"type": "keyword"},
                    "urgency_level": {"type": "keyword"},
                    "client_name": {"type": "text"},
                    "status": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "deadline_date": {"type": "date"}
                }
            }
        }
        
        await es.indices.create(index=index_name, body=mapping)
        print(f"✅ Created index: {index_name}")
        
        # Generate and index documents
        case_types = ["criminal", "civil", "corporate", "family", "immigration", "employment", "real_estate", "tax", "bankruptcy"]
        urgency_levels = ["critical", "high", "medium", "low"]
        clients = [fake.name() for _ in range(50)] + ["TechCorp Inc", "Legal Partners LLC", "State Attorney Office"]
        
        documents = []
        num_docs = 1000
        
        print(f"📝 Generating {num_docs} documents...")
        
        for i in range(num_docs):
            case_type = random.choice(case_types)
            urgency = random.choice(urgency_levels)
            created_date = fake.date_between(start_date='-1y', end_date='today')
            
            doc = {
                "id": str(uuid.uuid4()),
                "filename": f"{case_type}_{random.randint(1000, 9999)}.pdf",
                "content": f"Legal document for {case_type} case involving {random.choice(clients)}. " + fake.text(max_nb_chars=500),
                "case_type": case_type,
                "urgency_level": urgency,
                "client_name": random.choice(clients),
                "status": "complete",
                "created_at": created_date.isoformat(),
                "deadline_date": (created_date + timedelta(days=random.randint(1, 90))).isoformat() if urgency in ["high", "critical"] else None
            }
            documents.append(doc)
            
            if i % 100 == 0:
                print(f"Generated {i} documents...")
        
        print(f"✅ Generated {len(documents)} documents")
        
        # Bulk index using helpers
        print("🔍 Bulk indexing documents...")
        
        actions = []
        for doc in documents:
            action = {"_index": index_name, "_id": doc["id"], "_source": doc}
            actions.append(action)
        
        # Split into smaller batches
        batch_size = 50
        total_indexed = 0
        
        for i in range(0, len(actions), batch_size):
            batch = actions[i:i + batch_size]
            
            # Prepare bulk request body
            bulk_body = []
            for action in batch:
                bulk_body.append({"index": {"_index": action["_index"], "_id": action["_id"]}})
                bulk_body.append(action["_source"])
            
            try:
                response = await es.bulk(index=index_name, body=bulk_body)
                
                # Count successful operations
                for item in response["items"]:
                    if "index" in item and item["index"]["status"] in [200, 201]:
                        total_indexed += 1
                
                if (i // batch_size + 1) % 10 == 0:
                    print(f"Indexed {total_indexed} documents so far...")
                    
            except Exception as e:
                print(f"❌ Batch error: {e}")
        
        # Wait and refresh
        await asyncio.sleep(2)
        await es.indices.refresh(index=index_name)
        
        # Verify count
        count_result = await es.count(index=index_name)
        final_count = count_result["count"]
        
        print(f"✅ Successfully indexed {total_indexed} documents")
        print(f"📊 Final document count in Elasticsearch: {final_count}")
        
        # Show sample aggregations
        agg_result = await es.search(
            index=index_name,
            body={
                "size": 0,
                "aggs": {
                    "case_types": {"terms": {"field": "case_type", "size": 10}},
                    "urgency_levels": {"terms": {"field": "urgency_level"}}
                }
            }
        )
        
        print("\n📊 Document Distribution:")
        print("Case Types:")
        for bucket in agg_result["aggregations"]["case_types"]["buckets"]:
            print(f"  {bucket['key']}: {bucket['doc_count']}")
        
        print("Urgency Levels:")
        for bucket in agg_result["aggregations"]["urgency_levels"]["buckets"]:
            print(f"  {bucket['key']}: {bucket['doc_count']}")
        
        print(f"\n🎉 Demo data population completed!")
        print(f"🌐 Dashboard: http://localhost:3000")
        print(f"🔍 API: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await es.close()

if __name__ == "__main__":
    asyncio.run(populate_elasticsearch()) 