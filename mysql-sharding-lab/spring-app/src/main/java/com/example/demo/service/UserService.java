package com.example.demo.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.util.HashMap;
import java.util.Map;

@Service
public class UserService {

    @Autowired
    private JdbcTemplate shard0;

    @Autowired
    private JdbcTemplate shard1;

    @Autowired
    private StringRedisTemplate redis;

    public Map<String, Object> getUser(int id) {

        String cacheKey = "user:" + id;

        // 🔴 REDIS CHECK
        String cached = redis.opsForValue().get(cacheKey);

        if (cached != null) {
            Map<String, Object> res = new HashMap<>();
            res.put("source", "redis");
            res.put("data", cached);
            return res;
        }

        // 🧠 SHARD LOGIC
        JdbcTemplate db;
        String shard;

        if (id % 2 == 0) {
            db = shard0;
            shard = "shard0";
        } else {
            db = shard1;
            shard = "shard1";
        }

        String result = db.queryForObject(
            "SELECT name FROM users WHERE id=?",
            new Object[]{id},
            String.class
        );

        // 🔵 STORE IN REDIS
        redis.opsForValue().set(cacheKey, result);

        Map<String, Object> res = new HashMap<>();
        res.put("source", "db");
        res.put("shard", shard);
        res.put("data", result);

        return res;
    }
}