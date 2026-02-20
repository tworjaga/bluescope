//! Ring Buffer - High-performance circular buffer for packet storage

use std::sync::Mutex;

/// Lock-free ring buffer for packet storage
pub struct RingBuffer<T> {
    buffer: Mutex<Vec<Option<T>>>,
    capacity: usize,
    head: Mutex<usize>,
    tail: Mutex<usize>,
    size: Mutex<usize>,
}

impl<T: Clone> RingBuffer<T> {
    /// Create new ring buffer with specified capacity
    pub fn new(capacity: usize) -> Self {
        let mut buffer = Vec::with_capacity(capacity);
        for _ in 0..capacity {
            buffer.push(None);
        }

        Self {
            buffer: Mutex::new(buffer),
            capacity,
            head: Mutex::new(0),
            tail: Mutex::new(0),
            size: Mutex::new(0),
        }
    }

    /// Push item to buffer
    /// Returns false if buffer is full
    pub fn push(&self, item: T) -> bool {
        let mut size = self.size.lock().unwrap();
        
        if *size >= self.capacity {
            return false;
        }

        let mut head = self.head.lock().unwrap();
        let mut buffer = self.buffer.lock().unwrap();

        buffer[*head] = Some(item);
        *head = (*head + 1) % self.capacity;
        *size += 1;

        true
    }

    /// Pop item from buffer
    /// Returns None if buffer is empty
    pub fn pop(&self) -> Option<T> {
        let mut size = self.size.lock().unwrap();
        
        if *size == 0 {
            return None;
        }

        let mut tail = self.tail.lock().unwrap();
        let mut buffer = self.buffer.lock().unwrap();

        let item = buffer[*tail].take();
        *tail = (*tail + 1) % self.capacity;
        *size -= 1;

        item
    }

    /// Get current buffer size
    pub fn len(&self) -> usize {
        *self.size.lock().unwrap()
    }

    /// Check if buffer is empty
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Check if buffer is full
    pub fn is_full(&self) -> bool {
        self.len() >= self.capacity
    }

    /// Get buffer capacity
    pub fn capacity(&self) -> usize {
        self.capacity
    }

    /// Clear buffer
    pub fn clear(&self) {
        let mut buffer = self.buffer.lock().unwrap();
        let mut head = self.head.lock().unwrap();
        let mut tail = self.tail.lock().unwrap();
        let mut size = self.size.lock().unwrap();

        for item in buffer.iter_mut() {
            *item = None;
        }

        *head = 0;
        *tail = 0;
        *size = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ring_buffer_push_pop() {
        let buffer = RingBuffer::new(3);
        
        assert!(buffer.push(1));
        assert!(buffer.push(2));
        assert!(buffer.push(3));
        assert!(!buffer.push(4)); // Buffer full

        assert_eq!(buffer.pop(), Some(1));
        assert_eq!(buffer.pop(), Some(2));
        assert_eq!(buffer.pop(), Some(3));
        assert_eq!(buffer.pop(), None); // Buffer empty
    }

    #[test]
    fn test_ring_buffer_wrap_around() {
        let buffer = RingBuffer::new(3);
        
        buffer.push(1);
        buffer.push(2);
        buffer.pop();
        buffer.push(3);
        buffer.push(4);

        assert_eq!(buffer.pop(), Some(2));
        assert_eq!(buffer.pop(), Some(3));
        assert_eq!(buffer.pop(), Some(4));
    }
}
