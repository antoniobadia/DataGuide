import re
import json

#Basic function to return dictionary of counters based on common types
def counters():
    return {"int": 0, "str": 0, "float": 0, "date":0, "obj": 0, "arr": 0}

class Node:
    def __init__(self):
        """
        Initialization method for Node
        """
        #Children dictionary
        self.children = {}
        #Add counters dictionary
        self.counters = counters()

    def update_counter(self, type_name, delta=1):
        """
        Increases or decreases counter for the specific type input (based on delta)
        """
        #If the specific type is present in the node
        if type_name in self.counters:
            #increase or decrease counter
            self.counters[type_name] += delta
        #Fallback if unexpected type
        else:
            #set counter equal to delta
            self.counters[type_name] = delta
    
    def to_dict(self):
        """
        Method to convert node to dictionary for output
        """
        #Create children dictionary and fill with values
        children_dict = {key: child.to_dict() for key, child in self.children.items()}
        return {
            "counters": self.counters,
            "children": children_dict
        }

    @classmethod
    def from_dict(cls, d):
        """
        Class method to convert data guide text file to dictionary for output
        """
        #Create a new node
        node = cls()
        #Add counters to node
        node.counters = d.get("counters", counters())
        #Add children to node
        node.children = {key: cls.from_dict(child_dict) for key, child_dict in d.get("children", {}).items()}
        return node
    
class Path:
    def __init__(self, path_string):
        """
        Initialization method for Path
        """
        #Check if path input is string
        if not isinstance(path_string, str):
            raise TypeError("Path must be a string.")
        
        #Check if path input is root or empty string
        if path_string == "root" or path_string == "":
            #Set parts to empty list
            self._parts = []
        else:
            #Split path into individual parts
            self._parts = path_string.split('.')

    def __str__(self):
        """
        Returns the string representation of the path
        """
        #Return 'root' if no parts, otherwise join parts with '.'
        return "root" if not self._parts else ".".join(self._parts)

    def __repr__(self):
        """
        Returns a user friendly representation of the Path object
        """
        return f"Path('{str(self)}')"

    def __eq__(self, other):
        """
        Compares two Path objects for equality
        """
        #If other is not a Path object, return NotImplemented
        if not isinstance(other, Path):
            return NotImplemented
        #Return boolean based on if parts are equal
        return self._parts == other._parts

    def __hash__(self):
        """
        Enables Path objects to be used in sets and as dictionary keys
        """
        #Return hash of tuple of path parts
        return hash(tuple(self._parts))

    def get_parts(self):
        """
        Returns a list of the individual parts of the path
        """
        #Return copy of parts list
        return list(self._parts)

    def append(self, key):
        """
        Returns a new Path object with a new key appended
        """
        #If key is not a string or is empty, raise ValueError
        if not isinstance(key, str) or not key:
            raise ValueError("Key to append must be a non-empty string.")
        #Create a new list of parts
        new_parts = list(self._parts)
        #Append new key to parts list
        new_parts.append(key)
        #Return new Path object
        return Path(".".join(new_parts))
    
    def get_parent_path(self):
        """
        Returns a new Path object representing the parent path.
        Returns Path('root') if this path has only one part (e.g., 'a').
        Returns Path('root') if this path is already 'root'.
        """
        # If the path has no parts (it's the 'root' path), its parent is also 'root'
        if not self._parts: 
            return Path("root")
        # If the path has only one part (e.g., 'a'), its parent is 'root'
        if len(self._parts) == 1:
            return Path("root") 
        # Otherwise, join all parts except the last one to form the parent path
        return Path(".".join(self._parts[:-1]))

    def starts_with(self, prefix_path):
        """
        Checks if this path starts with the given prefix path.
        """
        # If prefix_path is not a Path object, return False
        if not isinstance(prefix_path, Path):
            return False
        
        # If this path is shorter than the prefix path, it cannot start with it
        if len(self._parts) < len(prefix_path._parts):
            return False
            
        # Check if the initial segment of this path matches the prefix path's parts
        return self._parts[:len(prefix_path._parts)] == prefix_path._parts
    
    def endswith(self, suffix):
        """
        Returns True if the path ends with the given suffix.
        The suffix can be a string or another Path object.
        """
        if isinstance(suffix, Path):
            return self.get_parts()[-len(suffix.get_parts()):] == suffix.get_parts()
        elif isinstance(suffix, str):
            return self.get_parts() and self.get_parts()[-1] == suffix
        return False

class DataGuidePath:
    def __init__(self):
        """
        Initialization method for DataGuide
        """
        self._array_lengths = {}
        #Create Node object for root
        self.root = Node()
        #Initialize document counter
        self.total_docs = 0

    def core(self):
        """
        Method to return core items from data guide
        -- A core item is one present in every document
        """
        #Create new data guide object for the core items
        core_guide = DataGuidePath()
        #Set the total documents of the core guide to that of the current guide
        core_guide.total_docs = self.total_docs
        #Call helper method to extract core items, starting from the root
        core_guide.root = self._extract_core(self.root)
        return core_guide
    
    def _extract_core(self, node):
        """
        Helper method to check if an item appears in every document
        """
        #Sum total count of types stored at the current node
        sum_counts = sum(node.counters.values())
        #Return None if the node's items are not present in every document
        if sum_counts != self.total_docs:
            return None
        #Create a new node to store the core items
        new_node = Node()
        #Copy core node's counters into the new core guide's node
        new_node.counters = node.counters.copy()
        #Iterate over children of the current node
        for key, child in node.children.items():
            #Recursive call on child nodes to find core children
            core_child = self._extract_core(child)
            #If a core child is found, add it to the new node's children
            if core_child is not None:
                new_node.children[key] = core_child
        return new_node
    
    def _get_type(self, value):
        """
        Helper method to return the type of data stored at a key
        """
        #Check if value is dictionary
        if isinstance(value, dict):
            return "obj"
        #Check if value is list
        elif isinstance(value, list):
            return "arr"
        #Check if value is integer
        elif isinstance(value, int):
            return "int"
        #Check if value is float
        elif isinstance(value, float):
            return "float"
        #Check if value is a string (date or string)
        elif isinstance(value, str):
            #Call helper method to check if string contains a date
            if self._is_date(value):
                return "date"
            #String does not contain a date
            else:
                return "str"
        else:
            #Fallback method, return type of value if not one included
            return type(value).__name__
        
    def _is_date(self, s):       
       """
       Helper method to check if a string is a date based on regular expression
       """
       #return boolean based on if input string is date
       return bool(re.match(r"\d{4}-\d{2}\d{2}", s))
    
    # modified to keep track of list lengths
    # Modified again to unpack nested lists
    def insert_document(self, *docs):
        """
        Insert one or more documents. Recursively unpacks nested lists.
        Example:
            insert_document(doc1, doc2)
            insert_document([doc1, doc2])  # also works
            insert_document(doc1, [doc2, doc3])  # mixed
        """
        if not hasattr(self, "_array_lengths"):
            self._array_lengths = {}

        def _handle(doc):
            if isinstance(doc, dict):
                self.total_docs += 1
                self._track_array_lengths(doc)
                self._insert_value(self.root, doc)
            elif isinstance(doc, list):
                for item in doc:
                    _handle(item)
            else:
                raise ValueError(f"Unsupported document type: {type(doc)}. Expected dict or list.")

        for doc in docs:
            _handle(doc)


    def _track_array_lengths(self, doc):
        """
        For each array field, record its length per document.
        Includes 0 for empty or None to support conservative expansion.
        """
        from collections import deque

        queue = deque([(Path(""), doc)])

        while queue:
            current_path, val = queue.popleft()
            if isinstance(val, dict):
                for k, v in val.items():
                    queue.append((current_path.append(k), v))
            elif isinstance(val, list):
                self._array_lengths.setdefault(str(current_path), []).append(len(val))
                for i in val:
                    queue.append((current_path.append("*"), i))
            elif val is None:
                self._array_lengths.setdefault(str(current_path), []).append(0)


    def _iter_all_paths(self):
        """
        Yields all (Path, Node) pairs in the guide.
        Useful for operations like scaling counters or printing.

        Example: for path 'root.customer.name', yields:
            (Path('customer.name'), <GuideNode>)
        """
        def _walk(node, path):
            yield path, node
            for key, child in node.children.items():
                yield from _walk(child, path.append(key))

        yield from _walk(self.root, Path(""))

    # Here value can be an entire document, a nested sub-object , a list, or a primitive value input through recursion
    def _insert_value(self, node, value): 
        """
        Helper method to insert a single value, called recursively on objects and arrays
        """
        #Check if current value is a dictionary (nested JSON object)
        if isinstance(value, dict):
            #Increment object counter
            node.update_counter("obj")
            #Iterate over keys and subvalues contained in object
            for key, subvalue in value.items(): # value.items() breaks down the value into its key pairs, such as 'a':1 , 'b': {'c':'foo'} etc.
                #Add key if not already present
                if key not in node.children:
                    node.children[key] = Node()
                #Recusive call for children
                self._insert_value(node.children[key], subvalue)
        #Check if current value is a list (array)
        elif isinstance(value, list):
            #Increment array counter
            node.update_counter("arr")
            #Add * to children if not already present
            if "*" not in node.children:
                node.children["*"] = Node()
            #Iterate over array elements
            for element in value:
                #Recursive call for array elements
                self._insert_value(node.children["*"], element)
        #Value is not object or array
        else:
            #Return type of value
            type_name = self._get_type(value)
            #Increase counter for value
            node.update_counter(type_name)

    def delete_document(self, doc):
        """
        Method to delete document from data guide
        """
        #Decrement document counter, ensure negative document amount does not occur
        self.total_docs = max(0, self.total_docs - 1)
        #Call helper method to update data guide
        self._delete_value(self.root, doc)

    def _delete_value(self, node, value):
        """
        Helper method to delete keys and decrement counters for a document
        """
        #Check if value is a dictionary (nested JSON object)
        if isinstance(value, dict):
            #Decrement object counter
            node.update_counter("obj", delta=-1)
            #Initialization of list to store keys to be removed
            keys_to_delete = []
            #Iterate over key value pairs
            for key, subvalue in value.items():
                #Check if key is in current nodes children
                if key in node.children:
                    #Recursive call to function for children nodes
                    self._delete_value(node.children[key], subvalue)
                    #Check if all counters are zero and node does not have any children
                    if all(count <= 0 for count in node.children[key].counters.values()) and not node.children[key].children:
                        #Add key to list for deletion
                        keys_to_delete.append(key)
            #Iterate of keys in list
            for key in keys_to_delete:
                #Remove key from children list
                del node.children[key]
        #Check if value is a list (array)
        elif isinstance(value, list):
            #Decrement array counter
            node.update_counter("arr", delta=-1)
            #Check for values stored in array
            if "*" in node.children:
                #Iterate over values stored in array
                for element in value:
                    #Recursive call to function for array elements
                    self._delete_value(node.children["*"], element)
                #Check if all counters are zero and array node does not have children
                if all(count <= 0 for count in node.children["*"].counters.values()) and not node.children["*"].children:
                    #Delete array children
                    del node.children["*"]
        #Not object or array
        else:
            #Return type stored
            type_name = self._get_type(value)
            #Update counter of type stored
            node.update_counter(type_name, delta=-1)
    
    def print_guide(self):
        """
        Method to print the data stored in a dataguide
        """
        #Submethod to print individual node in data guide
        def _print_node(node, path="root"):
            #Print key and counters dictionary for node
            print(f"{path}: {node.counters}")
            #Recursive call to function for child nodes
            for key, child in node.children.items():
                _print_node(child, path + "." + key)
        #Start by printing root node
        _print_node(self.root)

    def clear(self):
        """
        Method to clear dataguide when debugging
        """
        #Reset root node
        self.root = Node()
        #Reset total docs counter
        self.total_docs = 0

    def save(self, filename):
        """
        Method to save data guide as text file
        """
        #Open/Create file
        with open(filename, "w") as f:
            #Dump data guide contents to file as dictionary
            json.dump(self.to_dict(), f, indent=4)

    def to_dict(self):
        """
        Method to convert data guide to dictionary for output
        """
        #Recursive call to iterate through data guide and convert to dictionary
        return{
            "total_docs": self.total_docs,
            "root": self.root.to_dict()
        }

    @classmethod
    def from_dict(cls, d):
        """
        Class method to convert data guide dictionary to DataGuidePath object
        """
        #Create new data guide
        guide = cls()
        #Get total documents number from data guide dictionary
        guide.total_docs = d.get("total_docs", 0)
        #Set root node and recursively call function to iterate through data guide dictionary
        guide.root = Node.from_dict(d.get("root", {}))
        return guide

    @classmethod
    def load(cls, filename):
        """
        Class method to load a data guide text file as a data guide object
        """
        #Open text file
        with open(filename, "r") as f:
            #Load information
            d = json.load(f)
        #Convert from dictionary to data guide object
        return cls.from_dict(d)
    
    def difference(self, other):
        """
        Method to compute the difference between data guides
        """
        # Create result data guide to store difference
        result = DataGuidePath()
        # Get total document count and assign to new dataguide
        result.total_docs = self.total_docs
        
        # Call helper function on root nodes
        root_diff = self._subtract_nodes(self.root, other.root)
        # Assign root node if one exists, else empty node
        result.root = root_diff if root_diff is not None else Node()
        
        # Used to store number of unique keys
        uniques_total = 0
        
        # Gather paths in each data guide (these now return sets of Path objects)
        self_paths = set(self._gather_paths(self.root)) 
        other_paths = set(other._gather_paths(other.root))
        
        # Iterate over unique paths (Path objects can be in sets due to __hash__ and __eq__)
        for path_obj in self_paths - other_paths:
            # Get nodes of path (path_obj is passed directly to _traverse_path)
            node = self._traverse_path(path_obj)
            # If a node exists
            if node:
                # Sum unique counters
                uniques_total += sum(node.counters.values())
        
        # Object counter in root set to minimum between total documents and unique counters
        result.root.counters['obj'] = min(self.total_docs, uniques_total)
        
        # Ensures root atleast has one object
        result._ensure_root_obj()
        return result

    def _subtract_nodes(self, node1, node2):
        """
        Helper method to compare two nodes and subtract
        """
        #Create new node to store difference of nodes
        new_node = Node()
        #Iterate over counts in first input node
        for type, count1 in node1.counters.items():
            #Get counts for second input node
            count2 = node2.counters.get(type, 0) if node2 else 0
            #Calculate difference between counts
            diff = count1 - count2
            #Assign counters to new node
            new_node.counters[type] = diff if diff > 0 else 0
        #Iterate over children in first input node
        for key, child1 in node1.children.items():
            #Get children in second input node
            child2 = node2.children.get(key) if node2 and key in node2.children else None
            #If child2 exists
            if child2:
                #Recursive call for child nodes
                sub = self._subtract_nodes(child1, child2)
                #If child exist add to new node
                if sub is not None:
                    new_node.children[key] = sub
            #If there is no child2 node
            else:
                #Add entire subtree of children 
                new_node.children[key] = self._clone_subtree(child1)
        #If all counts are zero return no node
        if all(v == 0 for v in new_node.counters.values()) and not new_node.children:
            return None
        return new_node
    
    def _clone_subtree(self, node):
        """
        Helper method to copy an entire subtree of nodes when only one child
        """
        #Create new node
        copy = Node()
        #Copy counters dictionary from input node
        copy.counters = node.counters.copy()
        #Iterate over children of node
        for key, child in node.children.items():
            #Recursive call for child nodes
            copy.children[key] = self._clone_subtree(child)
        return copy
    
    def _sum_counters(self, node):
        """
        Method to return the sum of counters for path or data guide
        """
        #Create empty dictionary to store total counts
        total = {}
        #Iterate over key-value pairs (type and count) at the current node
        for key, value in node.counters.items():
            #Store key and sum counters
            total[key] = total.get(key, 0) + value
        #Iterate over children of the current node
        for child in node.children.values():
            #Recursive call to function to sum child node counters
            child_sum = self._sum_counters(child)
            #Iterate over key-value pairs in the child's sum dictionary
            for key, value in child_sum.items():
                #Store key and sum counters (aggregating counts from children)
                total[key] = total.get(key, 0) + value
        return total
    
    
    def nest(self, paths_to_project, new_root_key=None):
        """
        Returns a new DataGuidePath object containing only the specified paths.
        These paths can be provided as a list of Path objects or strings.
        If new_root_key is provided, all projected paths will be nested under this new key.

        Args:
            paths_to_project (list of Path or str): A list of Path objects or string representations of paths to project.
            new_root_key (str, optional): If provided, all projected paths will be nested
                                          under this new key at the root level.

        Returns:
            DataGuidePath: A new DataGuidePath object with only the matching paths.
        """
        processed_paths = []
        for p_input in paths_to_project:
            if isinstance(p_input, str):
                processed_paths.append(Path(p_input))
            elif isinstance(p_input, Path):
                processed_paths.append(p_input)
            else:
                raise TypeError("All items in paths_to_project must be Path objects or strings.")

        path_node_map = {}
        # We need to gather all *leaf* paths that are descendants of the paths_to_project
        # and then transform them if new_root_key is provided.
        
        all_original_leaf_paths = self._gather_paths(self.root)

        for original_leaf_path_obj in all_original_leaf_paths:
            source_node = self._traverse_path(original_leaf_path_obj)
            if source_node is None: continue # Should not happen if _gather_paths is correct

            # Check if this leaf path is a descendant of any of the paths_to_project
            should_include = False
            for project_path_obj in processed_paths:
                if original_leaf_path_obj.starts_with(project_path_obj):
                    should_include = True
                    break
            
            if should_include:
                transformed_path_obj = original_leaf_path_obj
                if new_root_key:
                    # If new_root_key is present, prepend it to the original path parts.
                    # Example: original path 'a.b.c', new_root_key 'X' -> 'X.a.b.c'
                    new_path_parts = [new_root_key] + original_leaf_path_obj.get_parts()
                    transformed_path_obj = Path(".".join(new_path_parts))
                
                path_node_map[transformed_path_obj] = source_node
        
        new_guide = self._rebuild_guide_from_path_node_map(path_node_map)
        new_guide.total_docs = self.total_docs
        return new_guide
    
    def nest_schema(self, grouping_paths=None, nest_specs=None, aggregations=None, new_path_for_others=None):
        """
        Supports:
        - grouping_paths: list of paths to keep at root (like 'deptid')
        - nest_specs: list of (newpath, list(path)) pairs (list(path) may be empty)
            → These define nested arrays where each entry contains those paths
        - new_path_for_others: fallback for legacy usage (e.g., group-and-nest-everything-else)
        """
        if not grouping_paths and not nest_specs:
            return DataGuidePath()

        grouping_paths = [Path(p) if isinstance(p, str) else p for p in (grouping_paths or [])]
        guides = []

        # 1. Retain grouping paths directly
        if grouping_paths:
            guides.append(self.nest(grouping_paths))

        # 2. Handle nest_specs: list of (newpath, list(path)) where list(path) may be empty
        if nest_specs:
            for newpath_raw, included_paths in nest_specs:
                newpath = Path(newpath_raw) if isinstance(newpath_raw, str) else newpath_raw

                # If included_paths is empty, gather all non-grouping paths
                if not included_paths:
                    all_paths = self._gather_paths(self.root)
                    included_paths = [
                        p for p in all_paths
                        if not any(p.starts_with(gp) for gp in grouping_paths)
                    ]

                guides.append(self._nest_struct_into_array(newpath, included_paths))

        # 3. Handle aggregation-only case (argument 2)
        if aggregations:
            guides.append(self._apply_aggregations(aggregations))

        # Merge all guide pieces
        if not guides:
            return DataGuidePath()

        result = guides[0]
        for g in guides[1:]:
            result = result.union(g)

        result.total_docs = self.total_docs
        max_docs_est, min_docs_est = self._estimate_doc_impact_bounds(grouping_paths, aggregations)
        result.max_docs_est = max_docs_est
        result.min_docs_est = min_docs_est


        return result
    
    def _nest_struct_into_array(self, new_array_path, paths_to_group):
        """
        Creates an array field under `new_array_path`, where each element is a struct (object)
        containing the full structure of each path in `paths_to_group`.

        Parameters:
            - new_array_path: Path where array will be created (e.g., 'emps')
            - paths_to_group: List of input paths to nest under `new_array_path.*`

        Returns:
            A new DataGuidePath with the nested array structure.
        """
        if not isinstance(new_array_path, Path):
            new_array_path = Path(new_array_path)

        processed_paths = [Path(p) if isinstance(p, str) else p for p in paths_to_group]
        path_node_map = {}
        all_leaf_paths = self._gather_paths(self.root)

        for leaf_path in all_leaf_paths:
            for group_root_path in processed_paths:
                if leaf_path.starts_with(group_root_path):
                    source_node = self._traverse_path(leaf_path)
                    if not source_node:
                        continue

                    # Create nested path like emps.*.emp.name
                    transformed_path = new_array_path.append("*")
                    for part in leaf_path.get_parts():
                        transformed_path = transformed_path.append(part)

                    path_node_map[transformed_path] = source_node
                    break  # skip to next leaf_path

        # ✅ Fix: ensure `new_array_path` itself is marked as an array
        array_node = Node()
        array_node.counters["arr"] = 1
        path_node_map[new_array_path] = array_node

        new_guide = self._rebuild_guide_from_path_node_map(path_node_map)
        new_guide.total_docs = self.total_docs
        return new_guide

    # Helper function for nest_schema
    def _estimate_doc_impact_bounds(self, grouping_paths, aggregations=None):
        """
        Estimate upper and lower bounds on the number of documents
        that could be impacted by a grouping + aggregation query.

        Returns:
            (max_est, min_est)
        """
        total = self.total_docs

        grouping_paths = [Path(p) if isinstance(p, str) else p for p in (grouping_paths or [])]
        aggregation_paths = [Path(p) if isinstance(p, str) else p for (_, p, _) in (aggregations or [])]

        group_counts = [self.get_path_count(p) for p in grouping_paths]
        agg_counts = [self.get_path_count(p) for p in aggregation_paths]

        # Conservative max: assume all docs with agg path contribute
        # (because grouping paths are almost always present)
        max_est = min(total, sum(agg_counts))

        # Conservative min: overlap of both sets
        if grouping_paths and aggregation_paths:
            min_est = min(
                min(group_counts, default=0),
                min(agg_counts, default=0)
            )
        else:
            min_est = min(group_counts + agg_counts + [0])

        return (max_est, min_est)
    
    #Helper function to _estimate_doc_impact_bounds
    def get_path_count(self, path):
        """
        Returns the total count of all values under the given path.
        Used for estimating document impact in grouping.
        """
        if isinstance(path, str):
            path = Path(path)
        elif not isinstance(path, Path):
            raise TypeError("Path must be a string or a Path object.")
        
        node = self._traverse_path(path)
        if not node:
            return 0
        return sum(node.counters.values())

    # Output function for _estimate_doc_impact_bounds
    def get_estimate_bounds(self):
        """
        Returns a dictionary with min/max doc estimates for the guide.
        Only available if generated by nest_schema.
        """
        return {
            "total_docs": getattr(self, "total_docs", None),
            "max_docs_est impacted": getattr(self, "max_docs_est", None),
            "min_docs_est impacted": getattr(self, "min_docs_est", None),
        }

    def union(self, other):
        """
        Method used to union two dataguides, other is a second dataguide
        """
        #Create new guide to store the union result
        new_guide = DataGuidePath()
        #Add total documents of both guides together and assign to the new guide
        new_guide.total_Docs = self.total_docs + other.total_docs
        #Call helper method to union the root nodes of both guides
        new_guide.root = self._union_nodes(self.root, other.root)
        return new_guide
    
    def _union_nodes(self, node1, node2):
        """
        Helper method used to combine two nodes, one from each guide, into new node
        """
        #Create new node to store combined key and value counts
        new_node = Node()
        # Get all unique types present in either node1 or node2's counters
        all_types = set(node1.counters.keys()) | set(node2.counters.keys())
        # Iterate over all collected types
        for t in all_types:
            # Combine counters of nodes for the current type
            new_node.counters[t] = node1.counters.get(t, 0) + node2.counters.get(t, 0)

        # Get all unique child keys present in either node1 or node2's children
        all_keys = set(node1.children.keys()) | set(node2.children.keys())
        # Iterate over all collected child keys
        for key in all_keys:
            # Get the child node for the current key from both input nodes
            child1 = node1.children.get(key)
            child2 = node2.children.get(key)

            # If both children exist for the current key
            if child1 and child2:
                # Recursively call _union_nodes to combine these children
                new_node.children[key] = self._union_nodes(child1, child2)
            # If only child1 exists for the current key
            elif child1:
                # Clone its entire subtree and add to the new node's children
                new_node.children[key] = self._clone_subtree(child1)
            # If only child2 exists for the current key
            elif child2:
                # Clone its entire subtree and add to the new node's children
                new_node.children[key] = self._clone_subtree(child2)
        return new_node



    def rename(self, old_path, new_path, inplace=False):
        """
        Rename all paths that start with `old_path` by replacing that prefix with `new_path`.

        Args:
            old_path (str or Path): path prefix to replace (e.g. "root.a" or "a.b")
            new_path (str or Path): replacement prefix (e.g. "root.a2" or "a2.b")
            inplace (bool): if True modify this DataGuidePath and return self,
                            if False (default) return a new DataGuidePath.

        Returns:
            DataGuidePath: the renamed DataGuidePath (self if inplace=True, else new object)

        Raises:
            TypeError: if path args are not str or Path.
            ValueError: if rename would cause path collisions (two original paths mapping to same target).
        """
        # Normalize inputs to Path objects
        if isinstance(old_path, str):
            old_p = Path(old_path)
        elif isinstance(old_path, Path):
            old_p = old_path
        else:
            raise TypeError("old_path must be a string or Path")

        if isinstance(new_path, str):
            new_p = Path(new_path)
        elif isinstance(new_path, Path):
            new_p = new_path
        else:
            raise TypeError("new_path must be a string or Path")
        
        if self.search(str(new_p)) and old_p != new_p:
            raise ValueError(f"Rename would cause a collision: '{str(new_p)}' already exists in the guide.")

        # Gather all paths (leaf and intermediate) from the guide
        all_paths = set()
        def _collect_all_paths_recursive(node, current_path_obj):
            if str(current_path_obj) != "":
                all_paths.add(current_path_obj)
            for key, child in node.children.items():
                _collect_all_paths_recursive(child, current_path_obj.append(key))
        _collect_all_paths_recursive(self.root, Path(""))
        
        # Build mapping from transformed_path -> source_node
        transformed_map = {}
        renamed_pairs = []  # tuples (old_str, new_str) for report
        
        # This set will track which original paths have been renamed, to avoid adding them as-is later.
        renamed_original_paths = set()

        # First pass: map all paths to their new name
        for orig_path_obj in all_paths:
            src_node = self._traverse_path(orig_path_obj)
            if src_node is None:
                continue

            if orig_path_obj.starts_with(old_p):
                suffix_parts = orig_path_obj.get_parts()[len(old_p.get_parts()):]
                new_parts = new_p.get_parts() + suffix_parts
                transformed_path_obj = Path(".".join(new_parts)) if new_parts else Path("")
                
                # Check for collisions during the mapping process as well
                if transformed_path_obj in transformed_map and transformed_map[transformed_path_obj] != src_node:
                    raise ValueError(f"Rename would create a collision: '{str(transformed_path_obj)}' from '{str(orig_path_obj)}' and another path.")
                
                transformed_map[transformed_path_obj] = src_node
                renamed_pairs.append((str(orig_path_obj), str(transformed_path_obj)))
                renamed_original_paths.add(orig_path_obj)

        # Second pass: add original paths that were not renamed
        for orig_path_obj in all_paths:
            if orig_path_obj not in renamed_original_paths:
                # Add only if not already in the map 
                if orig_path_obj not in transformed_map:
                    src_node = self._traverse_path(orig_path_obj)
                    if src_node:
                        transformed_map[orig_path_obj] = src_node
        
        # If nothing matched, return copy 
        if not renamed_pairs:
            if inplace:
                return self
            else:
                new_guide = self._rebuild_guide_from_path_node_map(transformed_map)
                new_guide.total_docs = self.total_docs
                return new_guide

        # Rebuild a new guide from the transformed_map
        new_guide = self._rebuild_guide_from_path_node_map(transformed_map)
        new_guide.total_docs = self.total_docs

        # Produce user feedback (up to 10 renamed)
        n_renamed = len(renamed_pairs)
        preview = renamed_pairs[:10]
        msg_lines = [f"Renamed {n_renamed} path(s)."]
        for old_s, new_s in preview:
            msg_lines.append(f"  {old_s} -> {new_s}")
        if n_renamed > 10:
            msg_lines.append(f"  ... (+{n_renamed-10} more)")

        report = "\n".join(msg_lines)
        print(report)

        if inplace:
            self.root = new_guide.root
            self.total_docs = new_guide.total_docs
            return self
        else:
            return new_guide


    def _get_top_level_segments(self):
        """
        Return a set of top-level keys present in the data guide (as Path objects).
        """
        tops = set()
        for p in self._gather_paths(self.root):
            parts = p.get_parts()
            if parts:
                tops.add(parts[0])
        return tops

    def _find_top_level_conflicts(self, other):
        """
        Return a sorted list of conflicting top-level key names (strings) between self and other.
        """
        if not isinstance(other, DataGuidePath):
            raise TypeError("other must be a DataGuidePath")
        s_tops = {t for t in self._get_top_level_segments()}
        o_tops = {t for t in other._get_top_level_segments()}
        conflicts = sorted(list(s_tops & o_tops))
        return conflicts

    def _auto_rename_top_level_conflicts(self, other, rename_prefix="__r"):
        """
        Make a copy of `other` and rename any top-level segments that conflict with self.
        Returns (other_copy, rename_map) where rename_map maps old_top -> new_top.
        """
        # copy other via dict roundtrip (safe shallow clone)
        other_copy = DataGuidePath.from_dict(other.to_dict())

        conflicts = self._find_top_level_conflicts(other_copy)
        used = set(self._get_top_level_segments())  # names already used on left

        rename_map = {}
        for top in conflicts:
            # generate candidate name by appending prefix + index until unique
            i = 1
            candidate = f"{top}{rename_prefix}{i}"
            while candidate in used:
                i += 1
                candidate = f"{top}{rename_prefix}{i}"
            used.add(candidate)
            # perform rename: we must rename top-level prefix `top` -> candidate
            old_prefix = top
            new_prefix = candidate

            # Build mapping of leaf paths to nodes for other_copy where prefix replaced
            all_leaf_paths = other_copy._gather_paths(other_copy.root)
            path_node_map = {}
            for leaf in all_leaf_paths:
                node = other_copy._traverse_path(leaf)
                if node is None:
                    continue
                parts = leaf.get_parts()
                if parts and parts[0] == old_prefix:
                    new_parts = [new_prefix] + parts[1:]
                    new_p = Path(".".join(new_parts))
                else:
                    new_p = leaf
                path_node_map[new_p] = node

            # rebuild other_copy from updated path map
            other_copy = other_copy._rebuild_guide_from_path_node_map(path_node_map)
            other_copy.total_docs = other.total_docs  # keep original doc count
            rename_map[old_prefix] = new_prefix

        return other_copy, rename_map


    def cartesian_product(self, other, rename_conflicts=False, rename_prefix="__r"):
        """
        Cartesian product of self and other.

        - If rename_conflicts=False (default): raises ValueError listing up to 10 conflicting top-level keys.
        - If rename_conflicts=True: auto-renames conflicting top-level keys on a copy of `other`
          using rename_prefix (default "__r"), reports the renames, then computes CP.

        Returns a new DataGuidePath.
        """
        if not isinstance(other, DataGuidePath):
            raise TypeError("other must be a DataGuidePath")
        if not isinstance(rename_conflicts, bool):
            raise TypeError("rename_conflicts must be a boolean value.")


        # detect top-level conflicts (list of strings)
        conflicts = self._find_top_level_conflicts(other)

        if conflicts and not rename_conflicts:
            # prepare message with up to 10 conflicts
            shown = conflicts[:10]
            more = len(conflicts) - len(shown)
            msg_lines = [f"Conflicting top-level keys detected ({len(conflicts)}):"]
            for c in shown:
                msg_lines.append(f"  - {c}")
            if more > 0:
                msg_lines.append(f"  ... and {more} more (showing first 10).")

            msg_lines.append("\nTo resolve this and rename path(s), set rename_conflicts=True.")
            raise ValueError("\n".join(msg_lines))

        # If renaming requested, create a renamed copy of other
        other_for_cp = other
        rename_map = {}
        if conflicts and rename_conflicts:
            other_for_cp, rename_map = self._auto_rename_top_level_conflicts(other, rename_prefix=rename_prefix)
            # Inform the user which top-levels were renamed
            if rename_map:
                info_lines = ["Auto-renamed conflicting top-level keys:"]
                for oldt, newt in rename_map.items():
                    info_lines.append(f"  - {oldt} -> {newt}")
                print("\n".join(info_lines))

        # Perform the CP operation:
        result = DataGuidePath()
        result.total_docs = self.total_docs * other_for_cp.total_docs

        # We'll use a single pass with a recursive helper to build the new guide
        result.root = self._cartesian_product_nodes(self.root, self.total_docs, other_for_cp.root, other_for_cp.total_docs)
        result._ensure_root_obj()
        return result
    
    def _rebuild_guide_from_map(self, path_node_map):
        """
        Rebuilds a new schema guide from the given path-to-node map.
        This helper correctly sets obj/arr counters for all intermediate nodes.
        """
        new_guide = DataGuidePath()
        
        temp_map = {path_obj: Node.from_dict(source_node.to_dict()) for path_obj, source_node in path_node_map.items()}

        for path_obj in sorted(temp_map.keys(), key=str):
            source_node = temp_map[path_obj]
            current_target_node = new_guide.root
            parts = path_obj.get_parts()

            for i, part in enumerate(parts):
                if part not in current_target_node.children:
                    current_target_node.children[part] = Node()

                if i == len(parts) - 1:
                    current_target_node.children[part].counters = source_node.counters.copy()
                
                if i < len(parts) - 1:
                    next_part = parts[i + 1]
                    if next_part == '*' and current_target_node.children[part].counters.get('arr', 0) == 0:
                        current_target_node.children[part].counters['arr'] = 1
                    elif next_part != '*' and current_target_node.children[part].counters.get('obj', 0) == 0:
                        current_target_node.children[part].counters['obj'] = 1

                current_target_node = current_target_node.children[part]
        
        return new_guide

    def _cartesian_product_nodes(self, node1, count1, node2, count2):
        """
        Helper to recursively merge and scale counters from two nodes for a cartesian product.
        """
        new_node = Node()

        all_dtypes = set(node1.counters.keys()) | set(node2.counters.keys())

        for dtype in all_dtypes:
            count1_val = node1.counters.get(dtype, 0)
            count2_val = node2.counters.get(dtype, 0)

            # For a cartesian product of schemaless documents,
            # a field present in one doc but not the other still exists in the result.
            # The count is the sum of their presence.
            if count1_val > 0 and count2_val > 0:
                # If both nodes have the data type, multiply their counts
                new_node.counters[dtype] = count1_val * count2_val
            elif count1_val > 0:
                # If only node1 has it, it gets scaled by the count of node2
                new_node.counters[dtype] = count1_val * count2
            elif count2_val > 0:
                # If only node2 has it, it gets scaled by the count of node1
                new_node.counters[dtype] = count2_val * count1

        # Merge children recursively
        all_keys = set(node1.children.keys()) | set(node2.children.keys())

        for key in all_keys:
            child1 = node1.children.get(key)
            child2 = node2.children.get(key)

            if child1 and child2:
                # Both children exist, so we perform a recursive cartesian product
                new_node.children[key] = self._cartesian_product_nodes(child1, count1, child2, count2)
            elif child1:
                # This subtree only exists in the first node, so it should be scaled by the count of the second node.
                new_node.children[key] = self._scale_subtree(child1, count2)
            elif child2:
                # This subtree only exists in the second node, so it should be scaled by the count of the first node.
                new_node.children[key] = self._scale_subtree(child2, count1)

        return new_node


    def _scale_subtree(self, node, multiplier):
        """
        Recursively clones and scales all counters in the subtree.
        """
        new_node = Node()
        for dtype, count in node.counters.items():
            new_node.counters[dtype] = count * multiplier

        for key, child in node.children.items():
            new_node.children[key] = self._scale_subtree(child, multiplier)

        return new_node

    def _rebuild_guide_from_path_node_map(self, path_node_map):
        """
        Helper to reconstruct a new DataGuidePath's tree from a map of
        transformed Path objects to their source Node objects.
        This will copy leaf counters. Parent 'obj' and 'arr' counters
        will be set to reflect structural presence (i.e., at least 1 if they have children)
        rather than summed document counts.
        """
        new_guide = DataGuidePath()

        # Sort paths to ensure consistent tree building order
        for path_obj in sorted(path_node_map.keys(), key=str):
            # Get the original node for this leaf
            source_node_for_leaf = path_node_map[path_obj] 
            
            current_target_node = new_guide.root
            parts = path_obj.get_parts()

            for i, part in enumerate(parts):
                # Create node if it doesn't exist
                if part not in current_target_node.children:
                    current_target_node.children[part] = Node()
                
                # Logic to set obj/arr for parents based on structural presence.
                # If a node now has children, it's an object (or contains an array if next is '*').
                if i < len(parts) - 1:
                    next_part = parts[i + 1]

                    if next_part == "*":
                        # Mark as array container
                        current_target_node.counters["arr"] = 1
                    else:
                        # Only mark as object if not already marked as array
                        if current_target_node.counters["arr"] == 0:
                            current_target_node.counters["obj"] = 1


                current_target_node = current_target_node.children[part]
            
            # At the leaf node, copy all its original counters directly
            current_target_node.counters = source_node_for_leaf.counters.copy()
        
        # Ensure the overall root's obj count is consistent if it has children
        new_guide._ensure_root_obj()
        return new_guide
    

    def card(self, path=None):
        """
        Method to extract cardinality from data guide.
        """
        # If no path is input, compute cardinality of the root
        if path is None:
            node = self.root
        else:
            # Determine if the input path is a string or a Path object and convert if necessary
            if isinstance(path, str):
                path_obj = Path(path)
            elif isinstance(path, Path):
                path_obj = path
            else:
                # Raise an error for invalid input type
                raise TypeError("Path must be a string or a Path object.")
            # Traverse the input path to get the target node
            node = self._traverse_path(path_obj)
            # If the node holds no values, return an empty counters dictionary
            if node is None:
                return counters()
        # Call _sum_counters method to get the total counts for the node and its subtree
        return self._sum_counters(node)
    
    def _traverse_path(self, path_obj): 
        """
        Helper method to move through a path, starting at the root node 
        and moving from child to child until path is complete or and end is reached
        """
        # If path_obj has no parts, it signifies the root
        if not path_obj.get_parts(): 
            return self.root
        
        current = self.root
        # Iterate through each part of the path object
        for part in path_obj.get_parts(): 
            # If the part is a child of the current node
            if part in current.children:
                # Move to the child node
                current = current.children[part]
            else:
                # If path part not found, return None
                return None
        # Return the final node at the end of the traversed path
        return current
    
    def _gather_paths(self, node, current_path_obj=None):
        """
        Helper method used to get all leaf paths connected to input node that have data.
        """
        paths = []
        # Create a starting path object for the current node's context
        # This will be 'root' for the initial call, or the path to the current node in recursion
        base_path = Path("") if current_path_obj is None else current_path_obj 

        # Iterate over key-child pairs in the current node's children
        for key, child in node.children.items():
            new_path_obj = base_path.append(key) # Build the full path to this child
            
            # Check if the child node is a leaf (has no children) AND has data counters
            if not child.children and sum(child.counters.values()) > 0:
                paths.append(new_path_obj)
            
            # Recursively gather paths from the child node, extending the current path
            paths.extend(self._gather_paths(child, new_path_obj))
        return paths

    def _path_contains_subpath(self, full_path_obj, sub_path_obj):
        """
        Checks if sub_path_obj exists as a contiguous sequence of parts anywhere within full_path_obj.
        Example: _path_contains_subpath(Path('a.b.c.d'), Path('b.c')) -> True
        Example: _path_contains_subpath(Path('a.b.c.d'), Path('x.y')) -> False
        """
        full_parts = full_path_obj.get_parts()
        sub_parts = sub_path_obj.get_parts()

        if not sub_parts: # An empty subpath is technically contained everywhere
            return True 
        if len(sub_parts) > len(full_parts):
            return False

        # Iterate through possible start positions in the full path
        for i in range(len(full_parts) - len(sub_parts) + 1):
            if full_parts[i:i + len(sub_parts)] == sub_parts:
                return True
        return False
    
    def _max_noncommon(self, all_paths, common_paths):
        """
        Helper method used to get maximum total sum of counters between all noncommon path nodes
        """
        # Variable to store the maximum total sum of counters
        n = 0
        # Iterate over paths that are in all_paths but not in common_paths
        for path_obj in all_paths - common_paths:
            # Get the node corresponding to the non-common path
            node = self._traverse_path(path_obj)
            # If a node exists
            if node:
                # Calculate the sum of all counter values for that node
                total = sum(node.counters.values())
                # If the current total is greater than the previously stored maximum, update n
                if total > n: 
                    n = total
        return n
    
    def _ensure_root_obj(self):
        """
        Helper method to ensure object counter in root node is atleast one when child nodes are present
        """
        # If the root's object counter is zero but it has children
        if self.root.counters['obj'] == 0 and self.root.children != {}:
            # Set the root's object counter to 1
            self.root.counters['obj'] = 1
    
    def search(self, path_input):
        """
        Search method, returns boolean based on if path is present in data guide
        """
        if isinstance(path_input, str):
            path_obj = Path(path_input)
        elif isinstance(path_input, Path):
            path_obj = path_input
        else:
            # Raise an error for invalid input type
            raise TypeError("Path must be a string or a Path object.")

        # Traverse the path to find the corresponding node
        node = self._traverse_path(path_obj)
        # Return True if the node is found (path exists), False otherwise
        return node is not None
    
    def nest_fields(self, parent_path_str, fields_to_nest_list, new_nested_key_name):
        """
        Nests a specific list of fields (and their sub-paths) under a new key.
        The fields in `fields_to_nest_list` must be direct children of `parent_path_str`.
        
        Example: nest_fields("root.user", ["address", "contact"], "details")
        'root.user.address.street' becomes 'root.user.details.address.street'
        'root.user.name' remains 'root.user.name'
        
        Returns a new DataGuidePath object with the transformed schema.
        
        Note: 'obj' and 'arr' counters for intermediate nodes in the new guide
        will reflect structural presence (i.e., at least 1 if they contain children/array elements)
        rather than summed document occurrences, as the transformation operates on schema, not original documents.
        Leaf node counters are preserved.
        """
        parent_path_obj = Path(parent_path_str)
        
        # Convert fields_to_nest_list to a set for efficient lookup
        fields_to_nest_set = set(fields_to_nest_list)

        path_node_map = {} # Map to store (transformed_path_obj: source_node)

        # Iterate through all leaf paths from the original guide
        all_original_paths = self._gather_paths(self.root)

        for original_path_obj in all_original_paths:
            source_node = self._traverse_path(original_path_obj)
            if source_node is None: continue 

            transformed_path_obj = original_path_obj

            # Check if this original path is under the parent_path_str
            if original_path_obj.starts_with(parent_path_obj):
                # Get the part of the path immediately following the parent_path_str
                # e.g., for original_path_obj="root.user.address.street", parent_path_obj="root.user"
                # first_segment_after_parent would be "address"
                parts_after_parent = original_path_obj.get_parts()[len(parent_path_obj.get_parts()):]
                
                if parts_after_parent: # Ensure there are parts after the parent path
                    first_segment_after_parent = parts_after_parent[0]

                    if first_segment_after_parent in fields_to_nest_set:
                        # This path needs to be nested.
                        # New path structure: parent_path + new_nested_key + (first_segment_after_parent + rest_of_parts)
                        transformed_path = parent_path_obj.append(new_nested_key_name)
                        for part in parts_after_parent: # Includes first_segment_after_parent itself
                            transformed_path = transformed_path.append(part)
                        transformed_path_obj = transformed_path
            
            path_node_map[transformed_path_obj] = source_node
        
        new_guide = self._rebuild_guide_from_path_node_map(path_node_map)
        new_guide.total_docs = self.total_docs 
        return new_guide

    def unnest_field(self, parent_path_str, field_to_unnest):
        """
        Unnests a specific field, lifting its children directly under its parent.
        The `field_to_unnest` must be a direct child of `parent_path_str`.
        
        Example: unnest_field("root.user", "location")
        'root.user.location.street' becomes 'root.user.street'
        'root.user.name' remains 'root.user.name'

        Returns a new DataGuidePath object with the transformed schema.
        
        Note: 'obj' and 'arr' counters for intermediate nodes in the new guide
        will reflect structural presence (i.e., at least 1 if they contain children/array elements)
        rather than summed document occurrences, as the transformation operates on schema, not original documents.
        Leaf node counters are preserved.
        """
        parent_path_obj = Path(parent_path_str)
        field_to_unnest_path_obj = parent_path_obj.append(field_to_unnest)

        path_node_map = {} 

        all_original_paths = self._gather_paths(self.root)

        for original_path_obj in all_original_paths:
            source_node = self._traverse_path(original_path_obj)
            if source_node is None: continue 

            transformed_path_obj = original_path_obj

            # Check if this original path starts with the field_to_unnest_path_obj (i.e., is a child of it)
            if original_path_obj.starts_with(field_to_unnest_path_obj):
                # Get the suffix parts (i.e., parts after the field_to_unnest_path_obj)
                # e.g., for original_path_obj="root.user.location.street", field_to_unnest_path_obj="root.user.location"
                # suffix_parts would be ["street"]
                suffix_parts = original_path_obj.get_parts()[len(field_to_unnest_path_obj.get_parts()):]
                
                # Build the new path: parent_path + suffix_parts
                transformed_path = parent_path_obj
                for part in suffix_parts:
                    transformed_path = transformed_path.append(part)
                transformed_path_obj = transformed_path
            
            path_node_map[transformed_path_obj] = source_node

        new_guide = self._rebuild_guide_from_path_node_map(path_node_map)
        new_guide.total_docs = self.total_docs 
        return new_guide
    
    def group_and_nest_non_grouping_keys(self, grouping_keys_to_keep, new_path_for_others):
        """
        Groups documents by 'grouping_keys_to_keep' (kept at their original level)
        and moves 'all other attributes' into a new array path.
        
        Args:
            grouping_keys_to_keep (list of str or Path): A list of paths (or string representations of paths)
                                                        to keep at their original top level.
            new_path_for_others (str): The name of the new path where all other attributes will be collected into an array. (e.g., 'e').

        Returns:
            DataGuidePath: A new DataGuidePath object with the transformed schema.
        """
        if not grouping_keys_to_keep:
            raise ValueError("grouping_keys_to_keep cannot be empty.")
        if not new_path_for_others:
            raise ValueError("new_path_for_others cannot be empty.")

        processed_grouping_key_paths = []
        for key in grouping_keys_to_keep:
            if isinstance(key, str):
                processed_grouping_key_paths.append(Path(key))
            elif isinstance(key, Path):
                processed_grouping_key_paths.append(key)
            else:
                raise TypeError("Each grouping key must be a string or a Path object.")

        transformed_path_node_map = {}
        all_original_leaf_paths = self._gather_paths(self.root)
        
        top_level_grouping_segments = {gp.get_parts()[0] for gp in processed_grouping_key_paths if gp.get_parts()}

        for original_path_obj in all_original_leaf_paths:
            source_node = self._traverse_path(original_path_obj)
            if source_node is None: continue 

            original_top_level_segment = original_path_obj.get_parts()[0] if original_path_obj.get_parts() else None
            
            # Case 1: Path is part of a grouping key's subtree. Keep it at its original level.
            is_part_of_kept_group = False
            for gp_obj in processed_grouping_key_paths:
                if original_path_obj.starts_with(gp_obj):
                    transformed_path_node_map[original_path_obj] = source_node
                    is_part_of_kept_group = True
                    break
            
            if not is_part_of_kept_group and original_top_level_segment:
                # Case 2: This path is NOT part of a grouping key's direct subtree,
                # AND its top-level segment is NOT one of the grouping keys.
                # So, it's an "other attribute" that needs to be nested under new_path_for_others.*
                # Example: 'a' -> 'e.*.a', 'f.*' -> 'e.*.f.*'
                
                # Check if this original_path_obj's top-level segment is NOT in the grouping keys.
                # This ensures we only move "other" top-level attributes.
                if original_top_level_segment not in top_level_grouping_segments:
                    transformed_path = Path(new_path_for_others).append('*')
                    # Append the entire original path after the '*'
                    for part in original_path_obj.get_parts(): 
                        transformed_path = transformed_path.append(part)
                    transformed_path_node_map[transformed_path] = source_node

        new_guide = self._rebuild_guide_from_path_node_map(transformed_path_node_map)
        new_guide.total_docs = self.total_docs
        
        return new_guide # Removed report output

    def project(self, paths_to_search_for, new_root_key=None):
        """
        Return a new DataGuide with only paths that contain any of the specified
        'paths_to_search_for' as a sub-path.
        Includes parent nodes as needed.
        The total_docs reflects the number of documents that *actually contribute*
        to the projected paths in the original guide.
        If new_root_key is provided, all projected paths will be nested under this new key.

        Args:
            paths_to_search_for (list of Path or str): A list of Path objects or string
                                                          representations of sub-paths to find and project.

        Returns:
            DataGuidePath: A new DataGuidePath object with the transformed schema.
        """
        path_node_map = {} 

        processed_search_paths = []
        for p_input in paths_to_search_for:
            if isinstance(p_input, str):
                processed_search_paths.append(Path(p_input))
            elif isinstance(p_input, Path):
                processed_search_paths.append(p_input)
            else:
                raise TypeError("All items in paths_to_search_for must be Path objects or strings.")
        
        all_original_leaf_paths = self._gather_paths(self.root) 

        matched_original_full_paths = set()
        for original_leaf_path_obj in all_original_leaf_paths:
            for search_sub_path_obj in processed_search_paths:
                # This aprt was once again updated so that the project total_docs only counts paths that start at the root.
                if original_leaf_path_obj.starts_with(search_sub_path_obj):
                    matched_original_full_paths.add(original_leaf_path_obj)
                    break 

        for original_full_path_obj in matched_original_full_paths:
            source_node = self._traverse_path(original_full_path_obj)
            if source_node: 
                transformed_path_obj = original_full_path_obj
                if new_root_key:
                    new_path_parts = [new_root_key] + original_full_path_obj.get_parts()
                    transformed_path_obj = Path(".".join(new_path_parts))
                path_node_map[transformed_path_obj] = source_node
            
        new_guide = self._rebuild_guide_from_path_node_map(path_node_map)
        
        # Calculate new_guide.total_docs: Sum of occurrences for all projected leaf paths.
        total_projected_occurrences = 0
        if matched_original_full_paths:
            for path_obj in matched_original_full_paths:
                node = self._traverse_path(path_obj)
                if node:
                    total_projected_occurrences += sum(node.counters.values())
            # Cap this sum at the original total_docs, but this is the value you want for total occurrences.
            new_guide.total_docs = min(self.total_docs, total_projected_occurrences)
        else:
            new_guide.total_docs = 0

        return new_guide

    def intersect(self, other):
        """
        Method to intersect two dataguides, as if an intersection was performed on original JSON documents
        """
        #Save document counts
        m1, m2 = self.total_docs, other.total_docs
        
        #Save paths of dataguides
        self_paths = set(self._gather_paths(self.root))
        other_paths = set(self._gather_paths(other.root))
        
        #Paths present in both dataguides
        common_paths = self_paths & other_paths

        #Number of paths in each dataguide not in other dataguide
        n1 = self._max_noncommon(self_paths, common_paths)
        n2 = self._max_noncommon(other_paths, common_paths)

        #Find minimum difference of document count to noncommon paths between guides
        #This is the number of documents present in the resulting intersection dataguide
        m_int = min(m1 - n1, m2 - n2)
        #Ensure m_int is not negative
        if m_int < 0: 
            m_int = 0
        
        #Create resulting dataguide and set total documents
        result = DataGuidePath()
        result.total_docs = m_int

        #Iterate over common paths, sorted by their string representation
        for path_obj in sorted(common_paths, key=str):
            #Get nodes of paths from both guides
            n1_node = self._traverse_path(path_obj) 
            n2_node = other._traverse_path(path_obj)
            #Dictionary used to combine common path counts
            comb = {}
            #Iterate over counters in nodes
            for t in set(n1_node.counters) | set(n2_node.counters):
                #Get counts of each type in each node
                c1 = n1_node.counters.get(t, 0)
                c2 = n2_node.counters.get(t, 0)
                #Get minimum count between common nodes
                val = min(c1, c2)
                #If value count is above zero, store count as minimum between value and document count
                if val > 0:
                    comb[t] = min(val, m_int)
                #Else store count as zero for that type
                else:
                    comb[t] = 0

            #If entire sum of values in comb dictionary is zero, move to next node
            if sum(comb.values()) == 0:
                continue

            #Set current node to root of the result guide
            current = result.root
            #Iterate over path parts
            for part in path_obj.get_parts(): 
                #Create new child node for current node if not already present
                current = current.children.setdefault(part, Node())
            #Set counters of current node to the combined counts
            current.counters = comb
        #Set root object counter to number of unique documents in the intersection
        result.root.counters['obj'] = m_int
        #Ensure root object counter has at least one node if there are children
        result._ensure_root_obj()
        
        return result  
    
    def _nest_matched_paths_and_filter_others(self, grouping_keys, new_nested_key_name, include_partial_or_null=False):
        """
        (Variant 1 of Group/Nest)
        Nests paths based on the presence of a set of 'grouping_keys' under a 'new_nested_key_name'.
        A path is considered for nesting if any part of its full path contains a grouping key.
        Everything else is either discarded (if include_partial_or_null=False) or moved to a partial/null bucket.
        
        Args:
            grouping_keys (list of str or Path): A list of paths (or string representations of paths)
                                                  that define the grouping criteria. These paths can
                                                  exist anywhere within the full path.
            new_nested_key_name (str): The name of the new key under which the grouped paths will be nested.
            include_partial_or_null (bool): If True, a "null" or "partial" grouping bucket will be created
                                            for paths that do not contain any specified grouping keys.
                                            This bucket will be named '_partial_or_null_group'.

        Returns:
            tuple: A tuple containing:
                - DataGuidePath: A new DataGuidePath object with the transformed schema.
                - dict: A report on grouping key presence, including estimations for impacted documents.
        """
        if not grouping_keys:
            raise ValueError("grouping_keys cannot be empty.")
        if not new_nested_key_name:
            raise ValueError("new_nested_key_name cannot be empty.")

        grouping_key_paths = []
        for key in grouping_keys:
            if isinstance(key, str):
                grouping_key_paths.append(Path(key))
            elif isinstance(key, Path):
                grouping_key_paths.append(key)
            else:
                raise TypeError("Each grouping key must be a string or a Path object.")

        transformed_path_node_map = {} 
        all_original_paths = self._gather_paths(self.root)
        
        for original_path_obj in all_original_paths:
            source_node = self._traverse_path(original_path_obj)
            if source_node is None: continue 

            is_matched_for_nesting = False
            for gp_obj in grouping_key_paths:
                if self._path_contains_subpath(original_path_obj, gp_obj):
                    is_matched_for_nesting = True
                    break
            
            if is_matched_for_nesting:
                transformed_path = Path(new_nested_key_name)
                for part in original_path_obj.get_parts():
                    transformed_path = transformed_path.append(part)
                transformed_path_node_map[transformed_path] = source_node
            elif include_partial_or_null:
                transformed_path = Path("_partial_or_null_group")
                for part in original_path_obj.get_parts():
                    transformed_path = transformed_path.append(part)
                transformed_path_node_map[transformed_path] = source_node
            # else: paths not matched and not for partial/null are implicitly discarded
        
        new_guide = self._rebuild_guide_from_path_node_map(transformed_path_node_map)
        new_guide.total_docs = self.total_docs

        # --- Report Generation ---
        max_impacted_documents_estimate = self.total_docs
        min_fuzzy_grouping_keys_present_estimate = 0
        if grouping_key_paths:
            fuzzy_key_total_docs_estimates = []
            for gp_obj in grouping_key_paths:
                fuzzy_key_total_docs_estimates.append(
                    self._estimate_docs_containing_any_fuzzy_key_occurrence(gp_obj)
                )
            if fuzzy_key_total_docs_estimates:
                min_fuzzy_grouping_keys_present_estimate = min(fuzzy_key_total_docs_estimates)
        
        report = {
            "total_documents_in_guide": self.total_docs,
            "max_impacted_documents_estimate": max_impacted_documents_estimate,
            "min_fuzzy_grouping_keys_present_estimate": min_fuzzy_grouping_keys_present_estimate,
            "grouping_key_presence_counts": {},
        }
        
        for gp_obj in grouping_key_paths:
            node = self._traverse_path(gp_obj)
            if node:
                report["grouping_key_presence_counts"][str(gp_obj)] = sum(node.counters.values())
            else:
                report["grouping_key_presence_counts"][str(gp_obj)] = 0
        
        return new_guide, report

    def _estimate_documents_with_subpath_intersection_union(self, primary_key_obj, fuzzy_subpath_obj):
        """
        Estimates the number of documents that contain the primary_key_obj
        AND any path that contains the fuzzy_subpath_obj.
        """
        if not isinstance(primary_key_obj, Path) or not isinstance(fuzzy_subpath_obj, Path):
            raise TypeError("Both primary_key_obj and fuzzy_subpath_obj must be Path objects.")

        all_original_leaf_paths = self._gather_paths(self.root)
        
        # Find all actual leaf paths in the guide that contain the fuzzy_subpath_obj
        actual_paths_containing_fuzzy_subpath = []
        for leaf_path_obj in all_original_leaf_paths:
            if self._path_contains_subpath(leaf_path_obj, fuzzy_subpath_obj):
                actual_paths_containing_fuzzy_subpath.append(leaf_path_obj)
        
        # Project the primary key once
        proj_primary_key_guide = self.project([primary_key_obj])

        estimated_union_total_docs = 0
    
        # Sum the estimated intersection counts for each pair.
        # This implicitly assumes the document sets for each (primary_key, actual_fuzzy_path) pair are mostly disjoint,
        # or it will overestimate the true union.
        for actual_fuzzy_path_obj in actual_paths_containing_fuzzy_subpath:
            # Project the current actual fuzzy path
            proj_actual_fuzzy_guide = self.project([actual_fuzzy_path_obj])
            
            # Get the estimated intersection count using the intuitive helper
            estimated_intersection_for_pair = self._get_intuitive_intersection_docs_count(
                proj_primary_key_guide, proj_actual_fuzzy_guide
            )
            
            estimated_union_total_docs += estimated_intersection_for_pair
            
        return estimated_union_total_docs
    
    def _get_intuitive_intersection_docs_count(self, guide1, guide2):
        """
        Helper to provide a more intuitive document intersection count for potentially disjoint schema paths.
        It estimates the intersection as the minimum of the total_docs of the two guides.
        This is a heuristic when precise overlap cannot be determined from schema alone.
        """
        # This estimate is based on the principle that the number of documents containing both sets of paths
        # cannot exceed the number of documents in the smaller of the two guides (assuming projection correctly sets total_docs).
        return min(guide1.total_docs, guide2.total_docs)

    def _estimate_docs_containing_any_fuzzy_key_occurrence(self, fuzzy_key_obj):
        """
        Estimates the total number of documents that contain at least one occurrence
        of the given fuzzy_key_obj (sub-path) anywhere within their full paths.
        This is a non-recursive version. It finds all relevant top-level keys
        and sums their document counts from the original guide.
        """
        if not isinstance(fuzzy_key_obj, Path):
            raise TypeError("fuzzy_key_obj must be a Path object.")

        all_original_leaf_paths = self._gather_paths(self.root)
        
        unique_top_level_segments_matched = set()
        for leaf_path_obj in all_original_leaf_paths:
            if self._path_contains_subpath(leaf_path_obj, fuzzy_key_obj):
                if leaf_path_obj.get_parts():
                    unique_top_level_segments_matched.add(Path(leaf_path_obj.get_parts()[0]))

        estimated_document_count = 0
        for top_level_path_obj in unique_top_level_segments_matched:
            node_at_top_level = self._traverse_path(top_level_path_obj)
            if node_at_top_level:
                estimated_document_count += sum(node_at_top_level.counters.values())
        
        return min(self.total_docs, estimated_document_count)

    def _get_intuitive_intersection_docs_count(self, guide1, guide2):

        """
        Helper to provide a more intuitive document intersection count for potentially disjoint schema paths.
        It estimates the intersection as the minimum of the total_docs of the two guides.
        This is a heuristic when precise overlap cannot be determined from schema alone.
        """
        # This estimate is based on the principle that the number of documents containing both sets of paths
        # cannot exceed the number of documents in the smaller of the two guides (assuming projection correctly sets total_docs).
        return min(guide1.total_docs, guide2.total_docs)
    
    def get_min_impact_estimate_for_grouping(self, grouping_keys_to_keep):
        """
        Calculates the minimum estimated number of documents that contain
        at least one of the specified grouping keys.
        This is used for reporting on the 'group_and_nest_non_grouping_keys' operation.
        """
        processed_grouping_key_paths = []
        for key in grouping_keys_to_keep:
            if isinstance(key, str):
                processed_grouping_key_paths.append(Path(key))
            elif isinstance(key, Path):
                processed_grouping_key_paths.append(key)
            else:
                raise TypeError("Each grouping key must be a string or a Path object.")

        min_kept_grouping_keys_present_estimate = 0
        if processed_grouping_key_paths:
            kept_key_total_docs_estimates = []
            for gp_obj in processed_grouping_key_paths:
                estimated_val = self._estimate_docs_containing_any_fuzzy_key_occurrence(gp_obj)
                kept_key_total_docs_estimates.append(estimated_val)
            
            kept_key_total_docs_estimates = [x for x in kept_key_total_docs_estimates if x is not None]

            if kept_key_total_docs_estimates:
                min_kept_grouping_keys_present_estimate = min(kept_key_total_docs_estimates)
            else:
                min_kept_grouping_keys_present_estimate = 0
        
        return min_kept_grouping_keys_present_estimate

    def get_estimated_docs_for_other_attributes_moved(self, grouping_keys_to_keep, new_path_for_others):
        """
        Estimates the number of documents that contain attributes that would be
        moved into the 'new_path_for_others' array by a grouping operation.
        """
        if not new_path_for_others:
            raise ValueError("new_path_for_others must be provided.")

        processed_grouping_key_paths = []
        for key in grouping_keys_to_keep:
            if isinstance(key, str):
                processed_grouping_key_paths.append(Path(key))
            elif isinstance(key, Path):
                processed_grouping_key_paths.append(key)
            else:
                raise TypeError("Each grouping key must be a string or a Path object.")

        all_original_leaf_paths = self._gather_paths(self.root)
        top_level_grouping_segments = {gp.get_parts()[0] for gp in processed_grouping_key_paths if gp.get_parts()}

        estimated_docs_with_other_attributes_moved = 0
        other_attributes_paths_for_report = set()
        for original_path_obj in all_original_leaf_paths:
            original_top_level_segment = original_path_obj.get_parts()[0] if original_path_obj.get_parts() else None
            is_part_of_kept_group = False
            for gp_obj in processed_grouping_key_paths:
                if original_path_obj.starts_with(gp_obj):
                    is_part_of_kept_group = True
                    break
            if not is_part_of_kept_group and original_top_level_segment and original_top_level_segment not in top_level_grouping_segments:
                other_attributes_paths_for_report.add(Path(original_top_level_segment)) 
        
        if other_attributes_paths_for_report:
            for path_obj in other_attributes_paths_for_report:
                estimated_docs_with_other_attributes_moved += self._estimate_docs_containing_any_fuzzy_key_occurrence(path_obj)
            estimated_docs_with_other_attributes_moved = min(self.total_docs, estimated_docs_with_other_attributes_moved)

        return estimated_docs_with_other_attributes_moved

    def _apply_aggregations(self, aggregation_specs):
        """
        Handles list of (fname, path, newpath) aggregation specs.
        Returns a new DataGuidePath with each aggregation result placed at `newpath`.
        """
        allowed_funcs = {"sum", "count", "avg", "min", "max"}
        path_node_map = {}

        for spec in aggregation_specs:
            if len(spec) != 3:
                raise ValueError("Each aggregation spec must be (fname, source_path, newpath)")

            fname, source_path_raw, target_path_raw = spec

            if fname not in allowed_funcs:
                raise ValueError(f"Unsupported aggregation function: {fname}")

            source_path = Path(source_path_raw)
            target_path = Path(target_path_raw)

            node = self._traverse_path(source_path)
            if not node:
                print(f"Skipping aggregation: {source_path} not found in guide.")
                continue

            # Create the output node
            agg_node = Node()

            # Determine output type
            if fname == "count":
                agg_node.counters["int"] = 1  # count is always int
            elif fname in {"sum", "avg"}:
                if node.counters.get("float", 0) or node.counters.get("int", 0):
                    agg_node.counters["float"] = 1
                else:
                    print(f"Skipping aggregation: {fname} cannot apply to non-numeric {source_path}")
                    continue
            elif fname in {"min", "max"}:
                found_type = None
                for t in ["int", "float", "str", "date"]:
                    if node.counters.get(t, 0):
                        found_type = t
                        break
                if not found_type:
                    print(f"Skipping aggregation: {fname} has no valid types for {source_path}")
                    continue
                agg_node.counters[found_type] = 1

            path_node_map[target_path] = agg_node

        if not path_node_map:
            print("No valid aggregation outputs were generated.")
            return DataGuidePath()

        # Build new guide
        new_guide = self._rebuild_guide_from_path_node_map(path_node_map)
        new_guide.total_docs = self.total_docs
        return new_guide


    def unnest_schema(self, unnest_specs=None):
        if not unnest_specs:
            return self

        final_path_node_map = {}
        all_original_paths_flat = set()
        all_paths_to_exclude = set()
        force_arr_paths = set()

        def _collect_all_paths(node, current_path_obj):
            if str(current_path_obj) != "":
                all_original_paths_flat.add(current_path_obj)
            for key, child in node.children.items():
                _collect_all_paths(child, current_path_obj.append(key))

        _collect_all_paths(self.root, Path(""))

        for source_array_path_raw, fields_to_unnest_list_raw in unnest_specs:
            source_array_path_obj = Path(source_array_path_raw)
            if not source_array_path_obj.endswith("*"):
                raise ValueError(f"Unnest path must end in '*': {source_array_path_obj}")

            fields_to_unnest_objs = [Path(p) for p in fields_to_unnest_list_raw]
            unnested_map = self._transform_paths_for_unnest_spec(source_array_path_obj, fields_to_unnest_objs)
            final_path_node_map.update(unnested_map)

            parent_path = source_array_path_obj.get_parent_path()
            force_arr_paths.add(parent_path)
            all_paths_to_exclude.add(parent_path)

            wildcard_prefix = source_array_path_obj.get_parts()
            for p in all_original_paths_flat:
                if p.get_parts()[:len(wildcard_prefix)] == wildcard_prefix:
                    all_paths_to_exclude.add(p)

        for p in all_original_paths_flat:
            if str(p) == "":
                continue  # ✅ skip root
            if p not in all_paths_to_exclude and p not in final_path_node_map:
                node = self._traverse_path(p)
                if node:
                    final_path_node_map[p] = node

        result_guide = self._rebuild_guide_for_unnest(
            final_path_node_map,
            force_arr_paths=force_arr_paths
        )

        # --- Conservative document expansion ---
        # --- Conservative document expansion ---
        expanded_count = 0
        for source_array_path_raw, _ in unnest_specs:
            parent_path = Path(source_array_path_raw).get_parent_path()
            lengths = self._array_lengths.get(str(parent_path), [])
            if lengths:
                expanded_count += sum(max(1, l) for l in lengths)
            else:
                expanded_count += self.total_docs  # fallback


        result_guide.total_docs = expanded_count

        # --- Scale original fields only ---
        flattened_paths_from_array = set(final_path_node_map) - set(all_original_paths_flat)

        if self.total_docs > 0 and expanded_count > 0:
            scale_factor = expanded_count / self.total_docs
            for path in final_path_node_map:
                if path in flattened_paths_from_array:
                    continue  # skip new unnested paths
                node = result_guide._traverse_path(path)
                if node:
                    for dtype in node.counters:
                        node.counters[dtype] = int(round(node.counters[dtype] * scale_factor))

        return result_guide
 
  
    def _transform_paths_for_unnest_spec(self, source_array_path_obj, fields_to_unnest_list_objs):
        """
        Transforms nested paths under a wildcard path (e.g., 'items.*') into flattened paths
        (e.g., 'items.qty') for the fields specified.

        Args:
            source_array_path_obj (Path): Path object ending in '*' indicating the array root.
            fields_to_unnest_list_objs (list of Path): Relative paths within the array elements to unnest.

        Returns:
            dict[Path, Node]: Mapping of new flattened paths to their corresponding nodes in the schema.
        """

        path_node_map = {}
        wildcard_parts = source_array_path_obj.get_parts()
        if not wildcard_parts or wildcard_parts[-1] != "*":
            raise ValueError(f"Expected array path to end with '*', got: {source_array_path_obj}")

        all_leaf_paths = self._gather_paths_for_unnest(self.root)
        wildcard_len = len(wildcard_parts)

        for leaf_path in all_leaf_paths:
            leaf_parts = leaf_path.get_parts()
            if leaf_parts[:wildcard_len] != wildcard_parts:
                continue

            relative_parts = leaf_parts[wildcard_len:]
            relative_path = Path(".".join(relative_parts)) if relative_parts else Path("")

            if not fields_to_unnest_list_objs or any(relative_path.starts_with(f) for f in fields_to_unnest_list_objs):
                base_parts = wildcard_parts[:-1]
                new_path = Path(".".join(relative_parts))

                node = self._traverse_path(leaf_path)
                if node:
                    path_node_map[new_path] = node

        return path_node_map

    def _rebuild_guide_for_unnest(self, path_node_map, force_arr_paths=None):
        new_guide = DataGuidePath()
        force_arr_paths = set(force_arr_paths or [])

        for path_obj in sorted(path_node_map.keys(), key=str):
            if str(path_obj) == "":
                continue  # ✅ skip root — handled manually in unnest_schema

            source_node = path_node_map[path_obj]
            current_node = new_guide.root
            parts = path_obj.get_parts()

            for i, part in enumerate(parts):
                if part not in current_node.children:
                    current_node.children[part] = Node()

                is_leaf = (i == len(parts) - 1)
                path_so_far = Path(".".join(parts[:i + 1]))

                if not is_leaf:
                    next_part = parts[i + 1]
                    if next_part == "*" or path_so_far in force_arr_paths:
                        current_node.counters["arr"] = 1

                current_node = current_node.children[part]

            current_node.counters = source_node.counters.copy()

        new_guide._ensure_root_obj()
        return new_guide


    def _gather_paths_for_unnest(self, node, current_path=None):
        """
        Recursively collects all leaf paths in the schema, starting from 'root',
        to support unnesting logic.

        Args:
            node (Node): The current schema node being traversed.
            current_path (Path): The path built up so far during recursion.

        Returns:
            list[Path]: All leaf paths found in the schema.
        """

        if current_path is None:
            current_path = Path("root")

        paths = []
        if not node.children:
            paths.append(current_path)
        for key, child in node.children.items():
            paths.extend(self._gather_paths_for_unnest(child, current_path.append(key)))
        return paths

        

        