# Pylon API

The Pylon API is responsible for handling the majority of data storage and customer interaction.

## Shell

Before using the shell its important to understand whats happening behind the scenes, especially with the added complexity of asyncio:

1. Before the shell starts we run the setup method for the web server
2. At no point is the teardown function called
3. Sitting on the readline blocks the asyncio loop

To open a shell simply run `bin/shell`.