Of course, here is the English translation of the document.

***

# Contribute to the GTPlanner Ecosystem

We firmly believe that an exceptional tool is built on the wisdom and collaboration of its community. GTPlanner's vision is to become a powerful assistant for every thinker, and this requires an open, robust, and ever-growing ecosystem. Whether you are a developer, a product manager, or a creative user, we sincerely invite you to join us in shaping the future of GTPlanner.

Every contribution you make, no matter how big or small, will become a powerful force driving the project forward. Here are a few ways we hope you'll get involved:

## 1. Contribute Tools: Expand the Planner's Knowledge Base

The core mission of GTPlanner is to generate a clear, high-quality planning blueprint for downstream AI programming (Vibe Coding). It does not execute code directly; instead, its role is to design the optimal implementation path for a specific task from a vast pool of available solutions.

Every tool you contribute **expands the library of solutions that GTPlanner knows, can use, and can recommend**. When GTPlanner has a thorough understanding of the specifications and usage of these tools (be they APIs, Python libraries, or other services), it can accurately reference and recommend them in the planning blueprint, leading to more professional and efficient solutions.

**Types of Tools You Can Contribute:**

*   **Platform Integrations:** Help GTPlanner understand how to use the capabilities of various platforms, such as the GitHub API, Notion SDK, or webhooks for Slack or Lark. This allows it to include steps for interacting with these platforms in its plans.
*   **Excellent Third-Party Tools:** Submit high-quality, verified third-party libraries or public APIs. Let GTPlanner know that when a specific problem arises, the community already has reliable, off-the-shelf solutions to recommend.
*   **Your Own Tools:** "Register" your own services or algorithms into GTPlanner's knowledge base. This enables GTPlanner to consider your unique data sources or private services as part of the solution when planning.

To help the community better understand the value of your tool, we highly recommend including a specific use case (Showcase) with your submission.

**Supported Tool Formats:**

*   **🌐 API Tools (API):** Encapsulate any public web API or REST service into a structured description. Based on this, GTPlanner will generate the correct instruction steps for calling the API in the planning document for downstream AI programming.
*   **📦 Python Packages (PYTHON_PACKAGE):** Register powerful PyPI libraries. This lets GTPlanner know when it should `import` and use a specific library in the planned code to solve a particular problem.
*   **🔌 MCP Services (MCP_SERVER):** If you have your own services that follow the MCP specification, you can integrate them. This allows GTPlanner to design complex interaction flows with your private services in its plans.

**How to Contribute?**

We use a simple YAML format to define the specifications and usage of each tool. You can easily contribute by filling out the template.

Here are two simple examples:

*   **API Tool Example (Query Weather):**
    *   *See example file: `tools/apis/example_openweather.yml`*
```yaml
id: "public.weather-api" 
type: "APIS" 
summary: "Get real-time weather information for cities worldwide." 
description: |   
  Through a public weather API, you can query detailed meteorological data 
  such as current weather, temperature, humidity, and wind speed for a specified city. 
  It's completely free to use, with no registration or API key required. 
base_url: "https://api.open-meteo.com/v1" 
endpoints:   
  method: "GET"     
  path: "/forecast"    
  summary: "Get current weather data based on latitude and longitude coordinates"
```

*   **Python Package Example (Video Downloader):**
    *   *See example file: `tools/python_packages/example_yt_dlp.yml`*
```yaml
id: "pypi.yt-dlp"
type: "PYTHON_PACKAGE"
summary: "A powerful video downloader that supports thousands of video sites."
description: |
  yt-dlp is an enhanced fork of youtube-dl, supporting video and audio 
  downloads from thousands of sites like YouTube, Bilibili, and Douyin.
requirement: "yt-dlp"
```

We believe that a powerful planner derives its strength from a comprehensive and high-quality knowledge base of tools. We have prepared a detailed **[PR template](.github/PULL_REQUEST_TEMPLATE/README.md)** for you and look forward to your participation!

---

## 2. Contribute Core Code: Prove Your Optimizations with Data

The heart of GTPlanner is its powerful planning and scheduling kernel. We welcome any code contributions that can make it smarter, more efficient, and more reliable. However, for a tool aimed at improving planning quality, "feeling better" is far from enough. We need objective evidence to validate the value of every improvement.

A convincing Pull Request consists not only of excellent code but also of clear evaluation results to prove that your changes have brought positive, measurable improvements to the final generated planning document. If you wish to improve GTPlanner's core algorithms, logical reasoning, or tool selection capabilities, we highly recommend that you:

*   **Embrace Benchmark-Driven Development:**
    Before you start modifying the code, first ask yourself, "How can I measure the impact of this optimization on the quality of the final planning document?" An ideal contribution workflow is:
    1.  Create one or a set of benchmark cases that can reproduce the current pain point (e.g., poor planning logic, incorrect tool selection).
    2.  Run the existing code on this benchmark, and record and save the generated planning document.
    3.  Submit your code changes.
    4.  Run the benchmark again and use a direct comparison of the old and new documents to clearly demonstrate your improvements.

*   **Include a Detailed Evaluation Report in Your PR:**
    Your PR description is key to convincing us. Please include:
    *   **Test Scenario:** A detailed description of the user requirement or problem scenario you used for testing.
    *   **Core Improvement Comparison:** Showcase your optimization results with specific examples. For instance: "This optimization reduced the average number of steps in the generated planning document by 15%, resulting in a clearer logic," or "On the newly introduced test case set, this change resolved the tool selection error issue present in the previous version."
    *   **Trade-off Analysis:** If your optimization involves any compromises (e.g., increased token consumption in exchange for stronger logical reasoning), please state them transparently.

*   **Contribute Reusable Benchmarks:**
    If you create a high-quality set of benchmark cases to validate your optimization, we strongly encourage you to contribute it to the community. This not only significantly strengthens the persuasiveness of your PR but also becomes a valuable asset for the project's future iterations.

We believe that every rigorously validated contribution is a solid push forward for the project. We look forward to your insightful and impactful code contributions.

---

## 3. Share Showcases: Inspire the Community and Build a Knowledge Base

Real-world use cases and best practices are the lifeblood of the project. Your experience not only inspires the community but also helps other users better understand and utilize GTPlanner, unlocking its full potential.

**We invite you to:**

*   **Submit Cool Applications to our Awesome List:** Add the interesting and practical applications or workflows you've built with GTPlanner to our **Awesome List** to spark more creativity.
*   **Write Tutorials or Blog Posts:** Share how you turned a vague idea into a reality, step by step, using GTPlanner. Your experience is invaluable to beginners.
*   **Share Your Conversation Cases:** Share a compelling conversation log with GTPlanner, telling the story of your project, your creation, and your thought process.

We are convinced that these concrete contributions will collectively pave the way for GTPlanner's progress, illuminating this map of vast potential, bit by bit. Thank you for your time and talent. We look forward to building with you