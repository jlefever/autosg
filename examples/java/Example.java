package com.example;

import java.util.List;
import java.util.ArrayList;

public class Example {
    private int count;
    private String name;

    public Example(String name) {
        this.count = 0;
        this.name = name;
    }

    public void increment() {
        count++;
    }

    public int getCount() {
        return count;
    }

    public static List<String> buildList(String[] items) {
        List<String> result = new ArrayList<>();
        for (String item : items) {
            result.add(item);
        }
        return result;
    }

    public static void main(String[] args) {
        Example ex = new Example("demo");
        ex.increment();
        System.out.println(ex.getCount());

        List<String> list = buildList(args);
        System.out.println(list.size());
    }
}
