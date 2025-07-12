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

class DataGuidePath:
    def __init__(self):
        """
        Initialization method for DataGuide
        """
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
    
    def insert_document(self, doc):
        """
        Method used to insert a document into data guide
        """
        #Check if JSON file contains multiple documents
        if isinstance(doc, list):
            #Iterate over documents in file
            for d in doc:
                self.total_docs += 1
                self._insert_value(self.root, d)
        #If single document
        elif isinstance(doc, dict):
            self.total_docs += 1
            self._insert_value(self.root, doc)

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
    
    #def nest(self, fuzzy_key_objs_list):
    #     """
    #     Returns a new DataGuidePath object containing only the leaf paths
    #     from the original guide that contain ANY of the given fuzzy_key_objs
    #     as a sub-path.
        
    #     Args:
    #         fuzzy_key_objs_list (list of Path): A list of Path objects to search for.

    #     Returns:
    #         DataGuidePath: A new DataGuidePath object with only the matching paths.
    #     """
    #     if not isinstance(fuzzy_key_objs_list, list):
    #         raise TypeError("fuzzy_key_objs_list must be a list of Path objects.")
    #     for key_obj in fuzzy_key_objs_list:
    #         if not isinstance(key_obj, Path):
    #             raise TypeError("All items in fuzzy_key_objs_list must be Path objects.")

    #     all_original_leaf_paths = self._gather_paths(self.root)
        
    #     paths_to_project = []
    #     for leaf_path_obj in all_original_leaf_paths:
    #         should_include_leaf = False
    #         for fuzzy_key_to_match in fuzzy_key_objs_list: # Iterate through the list of fuzzy keys
    #             if self._path_contains_subpath(leaf_path_obj, fuzzy_key_to_match): # Check if it contains ANY of them
    #                 should_include_leaf = True
    #                 break # Found a match for this leaf path, no need to check other fuzzy keys
            
    #         if should_include_leaf:
    #             paths_to_project.append(leaf_path_obj)
                
    #     return self.project(paths_to_project)

    # was working but has bugs removing for now
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
    
    # New method for nest_schema 07/10
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

                # Run nesting logic (updated _nest_struct_into_array will handle it)
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
        return result



    # latest method 12:36am 07/09 that is working, adding code to support argument 2
    #def nest_schema(self, paths_config, new_root_key=None, new_path_for_others=None):
        """
        Enhanced dispatcher: supports list of paths, or list of (newpath, [list of paths]).
        """
        if not paths_config:
            return DataGuidePath()
        
        # Detect tuple format: [(Path("newpath"), [Path("x.y"), Path("x.z")])]
        if all(isinstance(item, tuple) and len(item) == 2 for item in paths_config):
            # Multiple array structs to generate
            guides = []
            for new_array_path, group_paths in paths_config:
                if isinstance(new_array_path, str):
                    new_array_path = Path(new_array_path)
                guide = self._nest_struct_into_array(new_array_path, group_paths)
                guides.append(guide)
            
            # Union all the generated guides
            result = guides[0]
            for g in guides[1:]:
                result = result.union(g)
            return result
        
        # New code 07/09 12:38am to check:
        # Check for Argument Type 2: list of (fname, path, newpath)
        if all(isinstance(item, tuple) and len(item) == 3 and isinstance(item[0], str) for item in paths_config):
            fname_set = {item[0] for item in paths_config}
            if fname_set.issubset({"sum", "count", "avg", "min", "max"}):
                return self._apply_aggregations(paths_config)

        
        # Fallback to old behavior
        if new_path_for_others:
            if new_root_key:
                print("Warning: new_root_key is ignored when new_path_for_others is provided.")
            return self.group_and_nest_non_grouping_keys(paths_config, new_path_for_others)
        else:
            return self.nest(paths_config, new_root_key=new_root_key)


    #was working but needs modification 7/8/2025 12:34am removed
    # def nest_schema(self, paths_config, new_root_key=None, new_path_for_others=None):
        """
        A unified method to perform schema nesting based on the input configuration.

        Args:
            paths_config (list of Path or str):
                If `new_path_for_others` is NOT provided: Projects only the specified paths.
                                                          Equivalent to calling `self.nest(paths_config, new_root_key=new_root_key)`.
                If `new_path_for_others` IS provided: Groups documents by the paths in `paths_config` (kept at their original level)
                                                      and moves 'all other attributes' into the `new_path_for_others` array path.
                                                      Equivalent to calling `self.group_and_nest_non_grouping_keys(paths_config, new_path_for_others)`.
            new_root_key (str, optional): Only relevant when `new_path_for_others` is NOT provided.
                                          If provided, all projected paths will be nested under this new key.
            new_path_for_others (str, optional): Only relevant when `paths_config` is a list of paths to keep.
                                               The name of the new path where all other attributes will be collected into an array.

        Returns:
            DataGuidePath or tuple:
                - DataGuidePath: A new DataGuidePath object with the transformed schema.
                - If `group_and_nest_non_grouping_keys` is called, returns (DataGuidePath, dict) with a report.
        """
        if not isinstance(paths_config, list):
            raise TypeError("paths_config must be a list of Path objects or strings.")
        
        if not paths_config:
            return DataGuidePath() # Return empty if no paths are configured

        # Validate elements in paths_config
        for item in paths_config:
            if not isinstance(item, (Path, str)):
                raise TypeError("All items in paths_config must be Path objects or strings.")

        # Determine behavior based on presence of new_path_for_others
        if new_path_for_others:
            # Scenario: Group by paths_config, move others to new_path_for_others.*
            # In this case, new_root_key is not applicable.
            if new_root_key:
                print("Warning: new_root_key is ignored when new_path_for_others is provided, as behavior defaults to grouping.")
            
            # The paths_config itself contains the grouping_keys_to_keep
            grouping_keys_to_keep = paths_config 
            return self.group_and_nest_non_grouping_keys(grouping_keys_to_keep, new_path_for_others)
        else:
            # Scenario: Simple projection, possibly with a new root key
            # The paths_config contains the paths to project
            paths_to_project = paths_config
            return self.nest(paths_to_project, new_root_key=new_root_key)
    #adding new nest for testing 7/7/20225
    #def nest(self, paths_to_project, new_root_key=None):
        # This 'nest' method is now essentially a wrapper for 'project' with new_root_key
        # It's kept for backward compatibility with the `nest_schema` dispatcher logic.
        return self.project(paths_to_project, new_root_key=new_root_key)
    
    # new test updated 7/7/2025
    #def nest_schema(self, paths_config, new_root_key=None, new_path_for_others=None):
        """
        A unified method to perform schema nesting based on the input configuration.

        Args:
            paths_config (list of Path or str):
                If `new_path_for_others` is NOT provided: Projects only the specified paths (fuzzy match).
                                                          Effectively calls `self.project(paths_config, new_root_key=new_root_key)`.
                If `new_path_for_others` IS provided: Groups documents by the paths in `paths_config` (kept at their original level)
                                                      and moves 'all other attributes' into the `new_path_for_others` array path.
                                                      Effectively calls `self.group_and_nest_non_grouping_keys(paths_config, new_path_for_others)`.
            new_root_key (str, optional): Only relevant when `new_path_for_others` is NOT provided.
                                          If provided, all projected paths will be nested under this new key.
            new_path_for_others (str, optional): Only relevant when `paths_config` is a list of paths to keep.
                                               The name of the new path where all other attributes will be collected into an array.

        Returns:
            DataGuidePath or tuple:
                - DataGuidePath: A new DataGuidePath object with the transformed schema.
                - If `group_and_nest_non_grouping_keys` is called, returns (DataGuidePath, dict) with a report.
        """
        if not isinstance(paths_config, list):
            raise TypeError("paths_config must be a list of Path objects or strings.")
        
        if not paths_config:
            return DataGuidePath()

        for item in paths_config:
            if not isinstance(item, (Path, str)):
                raise TypeError("All items in paths_config must be Path objects or strings.")

        if new_path_for_others:
            if new_root_key:
                print("Warning: new_root_key is ignored when new_path_for_others is provided, as behavior defaults to grouping.")
            
            grouping_keys_to_keep = paths_config 
            return self.group_and_nest_non_grouping_keys(grouping_keys_to_keep, new_path_for_others)
        else:
            paths_to_project = paths_config
            # Call the now-updated project method, which handles fuzzy matching and new_root_key
            return self.project(paths_to_project, new_root_key=new_root_key)

    # new method to go with nest_schema testing 7/8/25, comminting out 07/11
    # def _nest_struct_into_array(self, new_array_path, paths_to_group):
        """
        Correctly nests multiple related paths into a single object inside an array.
        Ensures paths from the same top-level object are grouped under one `*` entry.
        """
        if not isinstance(new_array_path, Path):
            new_array_path = Path(new_array_path)

        processed_paths = [Path(p) if isinstance(p, str) else p for p in paths_to_group]

        path_node_map = {}
        all_leaf_paths = self._gather_paths(self.root)

        # Group all leaf paths that match any of the group_paths
        for group_path in processed_paths:
            for leaf_path in all_leaf_paths:
                if leaf_path.starts_with(group_path):
                    source_node = self._traverse_path(leaf_path)
                    if not source_node:
                        continue

                    suffix_parts = leaf_path.get_parts()[len(group_path.get_parts()):]
                    base_path = new_array_path.append("*")
                    for part in suffix_parts:
                        base_path = base_path.append(part)

                    # Include the matched group_path base itself
                    if not suffix_parts:
                        base_path = base_path.append(group_path.get_parts()[-1])

                    path_node_map[base_path] = source_node

        new_guide = self._rebuild_guide_from_path_node_map(path_node_map)
        new_guide.total_docs = self.total_docs
        return new_guide
    # updated to reflect wanted struture for DG 07/11
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

    """ ==== These methods use Path Class ==== """

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
                # Set obj/arr counter to 1 if it means it became a parent.
                # This signifies structural integrity, but not sum of original occurrences.
                # Start with if it's not the leaf itself
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

    # This project works as intended 07.10.2025 it updates the total_docs to account for only paths that start at the root
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

    # removing for now 7/7/2025 was working
    #def _estimate_docs_containing_any_fuzzy_key_occurrence(self, fuzzy_key_obj):
        """
        Estimates the total number of documents that contain at least one occurrence
        of the given fuzzy_key_obj (sub-path) anywhere within their full paths.
        This is done by projecting on all actual leaf paths that contain the fuzzy_key_obj
        and then taking the union of those projections' total_docs.
        """
        if not isinstance(fuzzy_key_obj, Path):
            raise TypeError("fuzzy_key_obj must be a Path object.")

        all_original_leaf_paths = self._gather_paths(self.root)
        
        # Collect the *unique top-level segments* of all actual leaf paths that contain the fuzzy_key_obj.
        # This is the most reliable way to count unique documents without document IDs.
        unique_top_level_segments_matched = set()
        for leaf_path_obj in all_original_leaf_paths:
            if self._path_contains_subpath(leaf_path_obj, fuzzy_key_obj):
                if leaf_path_obj.get_parts():
                    unique_top_level_segments_matched.add(Path(leaf_path_obj.get_parts()[0]))

        # Now, project on these unique top-level segments and union them.
        # This union's total_docs should represent the count of unique documents.
        union_of_projections_from_top_levels = DataGuidePath()
        for top_level_path_obj in unique_top_level_segments_matched:
            # Projecting on a top-level path should give total_docs for documents with that top-level path.
            proj_guide = self.project([top_level_path_obj])
            union_of_projections_from_top_levels = union_of_projections_from_top_levels.union(proj_guide)
            
        return union_of_projections_from_top_levels.total_docs
    # new mothod for testing
    #def _estimate_docs_containing_any_fuzzy_key_occurrence(self, fuzzy_key_obj):
        """
        Estimates the total number of documents that contain at least one occurrence
        of the given fuzzy_key_obj (sub-path) anywhere within their full paths.
        This is done by projecting on all actual leaf paths that contain the fuzzy_key_obj
        and then taking the union of those projections' total_docs.
        """
        if not isinstance(fuzzy_key_obj, Path):
            raise TypeError("fuzzy_key_obj must be a Path object.")

        all_original_leaf_paths = self._gather_paths(self.root)
        
        # Collect the *unique top-level segments* of all actual leaf paths that contain the fuzzy_key_obj.
        # This is the most reliable way to count unique documents without document IDs.
        unique_top_level_segments_matched = set()
        for leaf_path_obj in all_original_leaf_paths:
            if self._path_contains_subpath(leaf_path_obj, fuzzy_key_obj):
                if leaf_path_obj.get_parts():
                    unique_top_level_segments_matched.add(Path(leaf_path_obj.get_parts()[0]))

        # Now, project on these unique top-level segments and union them.
        # This union's total_docs should represent the count of unique documents.
        union_of_projections_from_top_levels = DataGuidePath()
        for top_level_path_obj in unique_top_level_segments_matched:
            # Projecting on a top-level path should give total_docs for documents with that top-level path.
            proj_guide = self.project([top_level_path_obj])
            union_of_projections_from_top_levels = union_of_projections_from_top_levels.union(proj_guide)
            
        return union_of_projections_from_top_levels.total_docs
    
    # new testing method 8:42pm 07/07/2025
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

    # New function 07/08 - 07/09 for arguement 2 in taking aggregates
    # def _apply_aggregations(self, aggregation_specs):
        """
        Handles list of (fname, path, newpath) aggregation specs.
        Implements validation and output type promotion.

        Returns:
            DataGuidePath: Transformed guide with new schema.
        """
        allowed_funcs = {"sum", "count", "avg", "min", "max"}
        numeric_funcs = {"sum", "avg"}
        all_funcs = {"sum", "count", "avg", "min", "max"}

        seen_newpaths = set()
        path_node_map = {}

        for spec in aggregation_specs:
            if len(spec) != 3:
                raise ValueError("Each aggregation spec must be a 3-tuple: (fname, path, newpath)")

            fname, source_path_raw, target_path_raw = spec

            if fname not in all_funcs:
                raise ValueError(f"Unsupported aggregation function: {fname}")

            source_path = Path(source_path_raw) if isinstance(source_path_raw, str) else source_path_raw
            target_path = Path(target_path_raw) if isinstance(target_path_raw, str) else target_path_raw

            if target_path in seen_newpaths:
                raise ValueError(f"Duplicate aggregation target path: {target_path}")
            seen_newpaths.add(target_path)

            node = self._traverse_path(source_path)
            if not node:
                print(f"Skipping: source path {source_path} not found in guide.")
                continue

            # Type validation based on aggregation function
            counters = node.counters
            if fname in numeric_funcs:
                if not (counters.get("int", 0) or counters.get("float", 0)):
                    #print(f"Skipping: cannot apply {fname} on non-numeric path {source_path}.")
                    continue
            elif fname in {"min", "max"}:
                if not any(t in counters for t in ("int", "float", "str", "date")):
                    #print(f"Skipping: {fname} not valid on {source_path} with types {list(counters.keys())}")
                    continue
            elif fname == "count":
                pass  # any type is allowed

            # Create output node with correct inferred type
            agg_node = Node()
            if fname == "count":
                agg_node.counters["int"] = 1
            elif counters.get("float", 0):
                agg_node.counters["float"] = 1
            elif counters.get("int", 0):
                # Even if int only, promote to float
                agg_node.counters["int"] = 1
            elif counters.get("date", 0):
                agg_node.counters["date"] = 1
            elif counters.get("str", 0):
                agg_node.counters["str"] = 1

            path_node_map[target_path] = agg_node

        new_guide = self._rebuild_guide_from_path_node_map(path_node_map)
        new_guide.total_docs = self.total_docs
        return new_guide

    # Even neweer helper function 07/10
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

    