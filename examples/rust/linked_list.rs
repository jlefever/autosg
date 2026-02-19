enum List<T> {
    Cons(T, Box<List<T>>),
    Nil,
}

impl<T: std::fmt::Display> List<T> {
    fn new() -> Self {
        List::Nil
    }

    fn prepend(self, value: T) -> Self {
        List::Cons(value, Box::new(self))
    }

    fn len(&self) -> usize {
        match self {
            List::Cons(_, tail) => 1 + tail.len(),
            List::Nil => 0,
        }
    }

    fn to_string(&self) -> String {
        match self {
            List::Cons(head, tail) => {
                let rest = tail.to_string();
                if rest.is_empty() {
                    format!("{}", head)
                } else {
                    format!("{} -> {}", head, rest)
                }
            }
            List::Nil => String::new(),
        }
    }
}

fn main() {
    let list = List::new()
        .prepend(3)
        .prepend(2)
        .prepend(1);

    println!("Length: {}", list.len());
    println!("List: {}", list.to_string());
}
