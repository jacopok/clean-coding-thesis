---
title: "Scientific coding best practices"
author: Jacopo Tissino
date: March 10, 2022
geometry: "left=3.5cm,right=3.5cm,top=3cm,bottom=3cm"
output: pdf_document
colorlinks: true
linkcolor: blue
---

What follows is a rough list of topics to touch on, 
which should be expanded on with detailed reasoning and examples.
The idea for the examples is as follows: try to write them consistently, in python,
and make them at least somewhat realistic --- give the reader a way to understand
how the patterns described can actually help their code.

Maybe mention external, proprietary tools which could be used for the more advanced stuff 
(e.g. Github Actions for continuous integration) but trying not to be too platform-specific,
giving alternatives.

# Index

## Generic

- the ideal requirements for code, in rough order of importance
	- doing what it's supposed to (!)
	- being tracked with a version control system (→ `git`)
	- documentation: other people (and you in 6 months' time) will know how to use it
	- testing (→ `pytest`, `tox`): it will be harder to make the code non-functional
	- using good software design, with a focus on maintainability and extensibility
    	- Refactoring code is much safer and easier if it comes after a suite
          of tests is already in place to check whether the changes are not 
          breaking existing functionality, which is why this is last
- the importance of open source software and science accessibility (→ `zenodo`)
- the interplay between rapid development and modularity/generality
	- discuss how the principles here should be taken with a grain of salt, in that
	- scientists are paid to write papers and not beautiful code
	- however, well-organized code can easily save time in the long run and avoid many headaches
	- maybe we can make some concrete examples?
- not reinventing the wheel: for many "common" problems, 
  somebody has already made a better solution than what you can make quickly

## Versioning

- use branches to develop new features!
- [semantic versioning](https://semver.org/) for public code: it's important 
  to have a consistent set of rules according to which the version number changes
- the same logic applies to [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/#specification)
- but, git logs are not changelogs: instead, make a proper [CHANGELOG](https://keepachangelog.com/en/1.0.0/)
- the possibility to use Continuous Integration (→ `tox`, CircleCI, Github Actions)
- semantic commits after many changes have been made using `git add --patch ...`
- using pre-commit hooks to make auto-formatting and other checks painless: 
  [`pre-commit`](https://pre-commit.com/) combined with 
  - `black` for auto-formatting, 
  - `flake8`, 
  - `mypy` for type checking,  
  - checking that no large files are being committed, and so on
- watch out for dependency management in modules! Document it (`pyproject.toml`), possibly in an 
	automated way (→ [`poetry`](https://python-poetry.org/))
- issue tracking: a clear pipeline for handling the inevitable problems
- having a paradigm for how branches are managed: 
  - for example, [git flow](https://nvie.com/posts/a-successful-git-branching-model/) 
    works for bigger projects with hard versioning and which need to maintain old 
    versions 
  - while [github flow](https://githubflow.github.io/) is simpler and works well
    for smaller projects, or ones with a continuous development schedule

## Testing

- having a proper test suite which can be run at will, as opposed to "ad hoc" tests
  of some property: code is really easy to break, and running all tests when something
  changes is a very good way to spot new problems which were introduced
  (-> `pytest`, `unittest`)
- also, half of the benefit of testing is that in order to be testable, 
  code needs to not be a tangled mess of interdependent stuff: 
  by testing the code, one is also forced to modularize it, thereby improving it
- property-based testing, as opposed to unit testing: test that with 
  "randomly chosen" inputs some condition holds, as opposed to just using
  some selected input-output pairs 
  (→ [`hypothesis`](https://hypothesis.readthedocs.io/en/latest/))
- parametrizing tests to check more behavior (→ `pytest.mark.parametrize`)
- benchmarking code inside the test suite (→ `pytest-benchmark`)
- using fixtures to simplify setup and tear-down
- test-driven development (for things whose purpose is already known, 
  which is not _always_ the case, but it should _often_ be)
- running tests with a debugger (→ [`pdb`](https://docs.python.org/3/library/pdb.html))
  - takes a while to get used to, but it makes finding issues way easier than
    inserting `print` statements everywhere
- measuring test coverage, not "to get 100%" but to get an idea
  of the thoroughness of the tests
  - maybe mention cleaver ideas like mutation testing 
    (→ [`mutmut`](https://mutmut.readthedocs.io/en/latest/)):
    a "test for your tests", in which the source code itself is randomly
    modified in certain places (say, change a number, negate a boolean...)
    and see whether the tests still pass --- if they do, they might not be
    capturing some issue with the code;

## Development and design patterns

- beautiful abstractions! when and how to use them (→ `abc` , `Protocol`)
  - decoupling _implementation_ from _usage_
- avoiding "magic numbers" in the code
- the DRY (don't repeat yourself) principle! 
  "if you're copy-pasting, you should feel like you're doing something dirty"
- the notion of "code smell" and technical debt
- SOLID principles for object-oriented design, when do they apply? 
  (this may not be the best way to approach the topic, 
  but it seems like a good summary of important things)
	- Single-responsibility: no huge classes
	- Open-closed: code should be open for addition, closed for modification: 
		- this means it should be able to be used in all* possible situations,
		  without needing to modify it
		- if functionality needs to be added, it should be possible to do so 
		  without changing the existing code
		- but, this is to be taken with a grain of salt: in "business" software development 
			one typically has a much better idea of what the code _should_ do than in science
			Still, it is good to keep in mind that _ideally_ this would be the case, 
			since it enables us to avoid writing code that we already know will need to be modified.
            For example, a parameter which we already know we will try several
            values for should not be hardcoded.
	- Liskov substitution: ability to substitute a parent class with its child
	- Interface segregation: decoupling, a part of the software should 
	  only need to care about the code it actually needs
	- Dependency inversion: "depend on abstractions, not on concretions"
- modules vs scripts in python: ideally, the combination should look like
	- module structure: large amount of code + no direct instructions in the code
	- script structure: small amount of code + direct instructions 
      (under an `if __name__ == '__main__'` clause)
	- modules for separating interface and implementation
	- scripts for testing and trying quick things
    	- also, jupyter notebooks work well for that sort of thing

## Readability

- write code optimized for human comprehension!
	- use `bool`s as opposed to `int` values of 1 and 0
	- give understandable names to variables
		- if these names are becoming very long, that could be a sign your
			code is not very modular
    - use `Enum`s as opposed to strings for 
      "things which can only take on a certain amount of values" 
- creating data structures for data which should always be together (→ `dataclass`)
  - this allows us to be versatile but consistent in creation as well:
    making `classmethod`s in the form `from_...`
- functional programming patterns 
    and how/when to use them in python (generators, `filter`, `map`, `reduce`)
  - these functions should have no side effects!

- static type checking the code is a good idea! (→ `mypy`):
    it can help catch bugs before they even have the possibility to occur
    python is easy to use with it being dynamically typed,
    but for large projects typing makes life much easier

- building documentation starting from the docstrings in the code (→ `sphinx` and so on)
  - in python, docstrings are used by the code itself, when calling `help`! 

- the principles of good documentation: the [Diátaxis Framework](https://diataxis.fr/)

## Optimization

- optimize with a scientific mindset: not blindly changing things, 
    but writing code, benchmarking/profiling it, 
    trying to improve what's taking the longest
    and testing to see whether it makes any difference
- the tricky business of benchmarking: your computer will not behave consistently!
    To get precise measurements, it's good to average out over several randomized runs.
    - the tools of the job (→ `cProfile`, 
      [`scalene`](https://github.com/plasma-umass/scalene), 
      not just `from time import perf_counter`!)
    - also [`snakeviz`](https://jiffyclub.github.io/snakeviz/) to visualize `cProfile` profiles
- don't optimize prematurely: it's often good to start by writing 
    the easy, naîve version of what you're thinking of
    and _then_, if it turns out that's too slow, change it!
    This avoids many instances of losing hours to write complex code which is a couple 
    milliseconds faster (or, sometimes, is actually slower) than the simple version
    which could have been written in much less time
- the tools for optimization, _when it's needed_:
  - caching
  - parallelization
  - threading
  - inserting compiled code within interpreted code 
    (→ [`numba`](https://numba.pydata.org/)) 

## Collaboration and asking questions

- even though I don't always agree with the tone, 
  [how to ask questions the smart way](http://www.catb.org/esr/faqs/smart-questions.html#translations)
  and [how to report bugs effectively](https://www.chiark.greenend.org.uk/~sgtatham/bugs.html) 
  are good references
- making a minimal reproducible example of your issue can result in you figuring out the problem
- contributing to open source projects