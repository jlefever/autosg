#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

template <typename T>
class SortedCollection {
public:
    void add(const T& item) {
        items_.push_back(item);
        std::sort(items_.begin(), items_.end());
    }

    const T& at(size_t index) const {
        return items_.at(index);
    }

    size_t size() const {
        return items_.size();
    }

    bool contains(const T& item) const {
        return std::binary_search(items_.begin(), items_.end(), item);
    }

    void print() const {
        for (const auto& item : items_) {
            std::cout << item << " ";
        }
        std::cout << std::endl;
    }

private:
    std::vector<T> items_;
};

int main() {
    SortedCollection<int> numbers;
    numbers.add(42);
    numbers.add(17);
    numbers.add(99);
    numbers.add(3);
    numbers.print();

    SortedCollection<std::string> words;
    words.add("banana");
    words.add("apple");
    words.add("cherry");
    words.print();

    return 0;
}
