from postgres import PostgresService

def quick_test():
    service = PostgresService()
    
    try:
        with service:
            # Test department summary
            print("\nFetching department summary...")
            dept_summary = service.get_department_summary(limit=3)
            print(f"\nTop 3 departments:")
            for dept in dept_summary:
                print(f"- {dept['department']}")
                print(f"  Projects: {dept['count']}")
                print(f"  Value: {dept['total_value_millions']:.2f}M")
                print()
    
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    quick_test()