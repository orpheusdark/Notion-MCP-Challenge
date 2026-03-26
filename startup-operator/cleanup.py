"""
Clean up old Notion dashboards from the parent page.
Archives all child page blocks (startup dashboards) to allow fresh starts.
"""

from config import Settings
from notion_client import Client

def cleanup_pages(settings: Settings) -> None:
    """Archive all child pages under the parent page."""
    client = Client(auth=settings.notion_api_key)
    
    # Get parent page's child blocks
    try:
        response = client.blocks.children.list(block_id=settings.notion_parent_page_id)
        results = response.get("results", [])
        
        count = 0
        for block in results:
            # Check if block is a child_page
            if block.get("type") == "child_page":
                page_id = block.get("id")
                try:
                    # Archive the page
                    client.pages.update(page_id=page_id, archived=True)
                    page_title = block.get("child_page", {}).get("title", "Unknown")
                    print(f"✓ Archived: {page_title}")
                    count += 1
                except Exception as e:
                    print(f"✗ Failed to archive page {page_id}: {e}")
        
        print(f"\nCleaned up {count} page(s) from Notion.")
        print("Ready for fresh start!")
        
    except Exception as e:
        print(f"Error accessing parent page: {e}")
        print("Manual cleanup: Go to your Notion page and archive the dashboards manually.")

if __name__ == "__main__":
    settings = Settings()
    cleanup_pages(settings)
