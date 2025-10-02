from data_analysis_agent import DataAnalysisAssistant

def main():
    agent = DataAnalysisAssistant()
    
    # Test web search
    print("\nTesting web search...")
    results = agent.web_search("linear regression diagnostics", max_results=2)
    for i, result in enumerate(results, 1):
        print(f"Result {i}:\n{result}\n")
    
    # Test file operations
    test_file = "test_data.csv"
    test_content = "Time,Value\n0,10\n1,20\n2,30"
    
    print(f"Writing to {test_file}...")
    agent.write_file(test_file, test_content)
    
    print(f"Reading from {test_file}...")
    file_contents = agent.read_file(test_file)
    print(f"File contents:\n{file_contents}")

if __name__ == "__main__":
    main()