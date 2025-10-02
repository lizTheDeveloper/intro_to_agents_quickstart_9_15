


## what we need for this agent 

- goal: what's the long horizon task we're trying to do?
- tools - what can we use to reach the goal?
- context - what's the current state, RAG, past actions, etc
- plan - requirements, or specs, or ways we'll reach the goal
- memory - where have we been, where are we in the plan, what's the recent state changes?


## book writer agent 

- goal: write a book about a given topic 
- tools: file writing, research- web search
- context: 
    - the book topic
    - the current outline for the book
    - research documents
    - a list of what we've researched so far
    - cached information from our research, and citations
    - the book's style, tone, and voice

- plan:
    - generate the plan for the resarch based on surface level research and the outline
    - iterate on the outline until we have a good outline, and a fair amount of cached information
    - write the book based on the outline and the cached information
    - given each chapter's content and an outline, write a first draft
    - iterate on the first draft until we have a good first draft
    - write the final draft
    
