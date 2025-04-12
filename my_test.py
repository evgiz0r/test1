import pygame
import sys
import random
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)

# Screen setup
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Binary Search Tree Visualization")

# Fonts
font = pygame.font.SysFont('Arial', 20)
large_font = pygame.font.SysFont('Arial', 36)

# Node class for BST
class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.x = 0
        self.y = 0
        # For tree visualization
        self.width = 1  # How many leaf positions this subtree takes

# Binary Search Tree class
class BST:
    def __init__(self):
        self.root = None
        self.next_value = self.generate_random_value()
        self.node_count = 0
        self.max_depth = 0
        # For zoom and pan
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        # Minimum distance between nodes at the same level
        self.min_node_distance = 40
        # For dynamic visualization sizing
        self.node_radius = 20
    
    def generate_random_value(self):
        return random.randint(1, 999)
    
    def insert(self, value):
        if self.root is None:
            self.root = Node(value)
        else:
            self._insert_recursive(self.root, value)
        
        # Calculate tree statistics and positions
        self.calculate_tree_info()
        
        # Generate the next value to insert
        self.next_value = self.generate_random_value()
    
    def _insert_recursive(self, current_node, value):
        if value < current_node.value:
            if current_node.left is None:
                current_node.left = Node(value)
            else:
                self._insert_recursive(current_node.left, value)
        elif value > current_node.value:
            if current_node.right is None:
                current_node.right = Node(value)
            else:
                self._insert_recursive(current_node.right, value)
        # If value == current_node.value, it's a duplicate, so we ignore it
    
    def calculate_tree_info(self):
        # Reset statistics
        self.node_count = 0
        self.max_depth = 0
        
        if self.root:
            # First, calculate subtree widths for proper spacing
            self._calculate_subtree_width(self.root)
            
            # Adjust node size based on tree size
            total_width = self.root.width if self.root else 1
            ideal_horizontal_spacing = 2 * self.min_node_distance
            self.node_radius = min(20, max(10, (WIDTH - 100) / (total_width * ideal_horizontal_spacing) * 15))
            
            # Then calculate positions
            vertical_spacing = min(80, max(40, (HEIGHT - 150) / (self._get_max_depth(self.root) + 1)))
            self._calculate_positions(self.root, 0, WIDTH, 0, vertical_spacing)
            
            # Update node count and max depth
            self.node_count = self._count_nodes(self.root)
            self.max_depth = self._get_max_depth(self.root)
    
    def _calculate_subtree_width(self, node):
        """Calculate the width of each subtree to determine proper horizontal spacing"""
        if node is None:
            return 0
        
        if node.left is None and node.right is None:
            node.width = 1
            return 1
        
        left_width = self._calculate_subtree_width(node.left)
        right_width = self._calculate_subtree_width(node.right)
        
        node.width = left_width + right_width
        return node.width
    
    def _count_nodes(self, node):
        if node is None:
            return 0
        return 1 + self._count_nodes(node.left) + self._count_nodes(node.right)
    
    def _get_max_depth(self, node, depth=0):
        if node is None:
            return depth - 1
        return max(self._get_max_depth(node.left, depth + 1), 
                  self._get_max_depth(node.right, depth + 1))
    
    def _calculate_positions(self, node, left_border, right_border, depth, vertical_spacing):
        """Calculate positions with width-based algorithm to prevent overlaps"""
        if node is None:
            return
        
        # Calculate node's horizontal position
        # The position is based on the relative width of the left subtree
        left_width = 0 if node.left is None else node.left.width
        right_width = 0 if node.right is None else node.right.width
        total_width = left_width + right_width
        
        if total_width == 0:
            # Leaf node
            node.x = (left_border + right_border) // 2
        else:
            # Calculate position based on the proportion of left subtree to total width
            proportion = left_width / total_width
            node.x = int(left_border + proportion * (right_border - left_border))
        
        # Calculate node's vertical position
        node.y = 120 + depth * vertical_spacing
        
        # Calculate positions for children
        if node.left:
            # Left child gets the left portion of the available space
            self._calculate_positions(node.left, left_border, node.x - self.min_node_distance, depth + 1, vertical_spacing)
        
        if node.right:
            # Right child gets the right portion of the available space
            self._calculate_positions(node.right, node.x + self.min_node_distance, right_border, depth + 1, vertical_spacing)
    
    def draw(self, screen):
        if self.root:
            # Create a node font based on node size
            font_size = max(12, min(16, int(self.node_radius * 0.8)))
            node_font = pygame.font.SysFont('Arial', font_size)
            
            # Draw the tree
            self._draw_recursive(screen, self.root, node_font)
    
    def _draw_recursive(self, screen, node, node_font):
        if node:
            # Draw connections to children first
            if node.left:
                pygame.draw.line(screen, BLACK, (node.x, node.y), (node.left.x, node.left.y), 2)
                self._draw_recursive(screen, node.left, node_font)
            
            if node.right:
                pygame.draw.line(screen, BLACK, (node.x, node.y), (node.right.x, node.right.y), 2)
                self._draw_recursive(screen, node.right, node_font)
            
            # Draw node
            pygame.draw.circle(screen, BLUE, (node.x, node.y), self.node_radius)
            pygame.draw.circle(screen, BLACK, (node.x, node.y), self.node_radius, 2)  # Border
            
            # Draw value
            text = node_font.render(str(node.value), True, WHITE)
            text_rect = text.get_rect(center=(node.x, node.y))
            screen.blit(text, text_rect)

# Create BST
bst = BST()

# Main game loop
def main():
    clock = pygame.time.Clock()
    
    while True:
        screen.fill(WHITE)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    bst.insert(bst.next_value)
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    # Insert multiple nodes at once for testing
                    for _ in range(10):
                        bst.insert(bst.next_value)
        
        # Draw the BST
        bst.draw(screen)
        
        # Display instructions and stats
        instructions1 = font.render("Click to insert the next number", True, BLACK)
        instructions2 = font.render("Press SPACE to insert 10 numbers at once", True, BLACK)
        screen.blit(instructions1, (10, 10))
        screen.blit(instructions2, (10, 40))
        
        # Display the next value to insert
        next_value_text = large_font.render(f"Next value: {bst.next_value}", True, RED)
        screen.blit(next_value_text, (WIDTH // 2 - next_value_text.get_width() // 2, 50))
        
        # Display node count
        if bst.node_count > 0:
            stats_text = font.render(f"Nodes: {bst.node_count}   Depth: {bst.max_depth}", True, BLACK)
            screen.blit(stats_text, (WIDTH - stats_text.get_width() - 10, 10))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()