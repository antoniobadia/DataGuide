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

class DataGuide:
    def __init__(self):
        """
        Initialization method for DataGuide
        """
        #Create Node object for root
        self.root = Node()
        #Initialize document counter
        self.total_docs = 0

    def search(self, path):
        """
        Search method, returns boolean based on if path is present in data guide
        """
        #Call helper method to move through path
        node = self._traverse_path(path)
        #Return boolean based on if path is present
        return node is not None

    def _traverse_path(self, path):
        """
        Helper method to move through a path, starting at the root node and moving from child to child until path is complete or and end is reached
        """
        #Check if path input is root, if so return root
        if not path or path == "root":
            return self.root
        #Split path into individual nodes
        parts = path.split('.')
        #Start at root node
        current = self.root
        #Iterate through nodes
        for part in parts:
            #Check if next node is a child of current node
            if part in current.children:
                current = current.children[part]
            else:
                #Return None if node not a child of current node
                return None
        #Return leaf node of path
        return current
    
    def _get_type(self, value):
        """
        Helper method to return the type of data stored at a key
        """
        #Check if value is dictionary (nested JSON object)
        if isinstance(value, dict):
            return "obj"
        #Check if value is list (array)
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

    def _insert_value(self, node, value): # Here value can be an entire document, a nested sub-object , a list, or a primitive value input through recursion
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
    
    #Not properly deleting documents#########################
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
        Class method to convert data guide text file to dictionary for output
        """
        #Create new data guide
        guide = cls()
        #Get total documents number from data guide text file
        guide.total_docs = d.get("total_docs", 0)
        #Set root node and recursively call function to iterate through data guide dictionary in text file
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
    
    def core(self):
        """
        Method to return core items from data guide
        -- A core item is one present in every document
        """
        #Create new data guide object for core
        core_guide = DataGuide()
        #Get total number of documents from data guide
        core_guide.total_docs = self.total_docs
        #Call extract core function to get core items
        core_guide.root = self._extract_core(self.root)
        return core_guide
    
    def _extract_core(self, node):
        """
        Helper method to check if an item appears in every document
        """
        #Sum total count of types stored at node
        sum_counts = sum(node.counters.values())
        #Return none if not a core node
        if sum_counts != self.total_docs:
            return None
        #Create a new node to store core nodes
        new_node = Node()
        #Copy core node into core data guide
        new_node.counters = node.counters.copy()
        #Iterate over children of node
        for key, child in node.children.items():
            #Recursive call on child nodes
            core_child = self._extract_core(child)
            #Add core children to core node if a core child
            if core_child is not None:
                new_node.children[key] = core_child
        return new_node
    
    def card(self, path=None):
        """
        Method to extract cardinality from data guide
        """
        #If no path is input, compute cardinality of root
        if path is None:
            node = self.root
        #Path is input
        else:
            #Traverse input path
            node = self._traverse_path(path)
            #If node holds no values return empty counters dictionary
            if node is None:
                return counters()
        #Call sum counters method
        return self._sum_counters(node)
    
    def _sum_counters(self, node):
        """
        Method to return the sum of counters for path or data guide
        """
        #Create empty total dictionary
        total = {}
        #Iterate over key value pairs at node
        for key, value in node.counters.items():
            #Store key and sum counters
            total[key] = total.get(key, 0) + value
        #Iterate over children of node
        for child in node.children.values():
            #Recusive call to function to sum child node counters
            child_sum = self._sum_counters(child)
            #Iterate over key value pairs in child sum dictionary
            for key, value in child_sum.items():
                #Store key and sum counters
                total[key] = total.get(key, 0) + value
        return total
    
    def union(self, other):
        """
        Method used to union two dataguides, other is a second dataguide
        """
        #Create new guide to store union
        new_guide = DataGuide()
        #Add total docs of each guide together and assign
        new_guide.total_Docs = self.total_docs + other.total_docs
        #Call helper method to union the nodes
        new_guide.root = self._union_nodes(self.root, other.root)
        return new_guide
    
    def _union_nodes(self, node1, node2):
        """
        Helper method used to combine two nodes, one from each guide, into new node
        """
        #Create new node to store key and value counts
        new_node = Node()
        #Get all stored types of each node input into method
        all_types = set(node1.counters.keys()) | set(node2.counters.keys())
        #Iterate over types
        for t in all_types:
            #Combine counters of nodes
            new_node.counters[t] = node1.counters.get(t, 0) + node2.counters.get(t, 0)
        #Get all child keys of root nodes
        all_keys = set(node1.children.keys()) | set(node2.children.keys())
        #Iterate over child keys
        for key in all_keys:
            #Get first two child keys
            child1 = node1.children.get(key)
            child2 = node2.children.get(key)
            #If both keys are the same
            if child1 and child2:
                #Recursive call on child nodes
                new_node.children[key] = self._union_nodes(child1, child2)
            #If child1 key is present
            elif child1:
                #Add child key to current node's children
                new_node.children[key] = child1
            #If child2 key is present
            elif child2:
                #Add child key to current node's children
                new_node.children[key] = child2
        return new_node
    
    def difference(self, other):
        """
        Method to compute the difference between data guides
        """
        #Create result data guide to store difference
        result = DataGuide()
        #Get total document count and assign to new dataguide
        result.total_docs = self.total_docs
        #Call helper function on root nodes
        root_diff = self._subtract_nodes(self.root, other.root)
        #Assign root node if one exists, else empty node
        result.root = root_diff if root_diff is not None else Node()
        #Used to store number of unique keys
        uniques_total = 0
        #Gather paths in each data guide
        self_paths = set(self._gather_paths(self.root))
        other_paths = set(self._gather_paths(other.root))
        #Iterate over unique paths
        for path in self_paths - other_paths:
            #Get nodes of path
            node = self._traverse_path(path)
            #If a node exists
            if node:
                #Sum unique counters
                uniques_total += sum(node.counters.values())
        #Object counter in root set to minimum between total documents and unique counters
        result.root.counters['obj'] = min(self.total_docs, uniques_total)
        #Ensures root atleast has one object
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
    
    def project(self, paths):
        """
        Return a new DataGuide with only the specified (possibly nested) paths.
        Includes parent nodes as needed. Updates total_docs to reflect the
        minimum number of documents that could contain all projected paths.
        """
        new_guide = DataGuide()
        min_counts = []

        for path in paths:
            #Check if full path exists
            source_leaf = self._traverse_path(path)
            if source_leaf is None:
                #Skip nonexistent paths
                continue  
            #Track the total count for this path
            min_counts.append(sum(source_leaf.counters.values()))

            #Traverse parts of the path
            parts = path.split(".")
            source_node = self.root
            target_node = new_guide.root

            for part in parts:
                if part not in source_node.children:
                    break

                if part not in target_node.children:
                    target_node.children[part] = Node()

                source_node = source_node.children[part]
                target_node = target_node.children[part]

                #Copy counters at every level
                target_node.counters = source_node.counters.copy()

        #Conservative max total docs that might have any of the paths
        sum_counts = sum(min_counts)
        new_guide.total_docs = min(self.total_docs, sum_counts)
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
        result = DataGuide()
        result.total_docs = m_int

        #Iterate over common paths
        for path in sorted(common_paths):
            #Get nodes of paths
            n1_node = self._traverse_path(path)
            n2_node = other._traverse_path(path)
            #Comb dictionary used to combine common path counts
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

            #Set current node to root
            current = result.root
            #iterate over path nodes
            for part in path.split('.'):
                #Create new child node for current node
                current = current.children.setdefault(part, Node())
            #Set counters of current node to comb dictionary
            current.counters = comb
        #Set root object counter to number of unqiue documents
        result.root.counters['obj'] = m_int
        #Ensure root object counter has at least one node
        result._ensure_root_obj()
        
        return result
    
    def _gather_paths(self, node, prefix=""):
        """
        Helper method used to get all paths connected to input node
        """
        #Create paths list
        paths = []
        #Iterate over key value pairs of child nodes
        for key, child in node.children.items():
            #Add key to path, if prefix is present then add prefix with new key added
            path = key if not prefix else prefix + "." + key
            #Add path to paths list
            paths.append(path)
            #Recursive call with child node and prefix
            paths.extend(self._gather_paths(child, path))
        return paths
    
    def _max_noncommon(self, all_paths, common_paths):
        """
        Helper method used to get maximum total sum of counters between all noncommon path nodes
        """
        #n used to store maximum total sum of counters
        n = 0
        #Iterate over noncommon paths
        for path in all_paths - common_paths:
            #Get nodes of noncommon paths
            node = self._traverse_path(path)
            #If node is returned
            if node:
                #Sum all counter values
                total = sum(node.counters.values())
                #If current total is bigger than previous max, replace n
                if total > n: 
                    n = total
        return n
    
    def _ensure_root_obj(self):
        """
        Helper method to ensure object counter in root node is atleast one when child nodes are present
        """
        if self.root.counters['obj'] == 0 and self.root.children != {}:
            self.root.counters['obj'] = 1