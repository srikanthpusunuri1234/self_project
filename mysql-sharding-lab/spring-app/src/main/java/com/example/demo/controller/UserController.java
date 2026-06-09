package com.example.demo.controller;

import com.example.demo.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
public class UserController {

    @Autowired
    private UserService service;

    @GetMapping("/user/{id}")
    public Map<String, Object> get(@PathVariable int id) {
        return service.getUser(id);
    }
}