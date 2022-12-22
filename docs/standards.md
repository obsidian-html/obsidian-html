# Code Standards
## 1. Class, function and method naming
### 1.1 Functions and methods use snake_case
Reason: nice to have standards.
Exception: VeryImportantHighLevelFunctionsUseCamelCase, e.g. ConvertVault

### 1.2 Classes use CamelCase
Reason: Good to delineate between classes and instances (e.g. Config vs config)

### 1.3 Type hinting types use CamelCase and are imported via T
e.g.:
    from .core import Types as T
    def bla() -> T.RTRPosX

### 1.4 Functions and methods use verb-noun naming
So "GetThing", "check_kettle", etc
"Do" is not allowed as a verb!

## 2. Type Hinting
### 2.1 Type hinting is voluntary
Adding types can sometimes really help in quickly parsing a function, but are not yet useful enough to put everywhere.

### 2.2 When using type hinting, use v4.Types
Reason: the whole idea of using types is to make contracts. Contracts require every part of the code talking the same language.