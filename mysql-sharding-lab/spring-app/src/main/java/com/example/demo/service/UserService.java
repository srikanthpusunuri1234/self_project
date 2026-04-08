package com.example.demo.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

@Service
public class UserService {

    @Autowired
    @Qualifier("shard0")
    private JdbcTemplate shard0;

    @Autowired
    @Qualifier("shard1")
    private JdbcTemplate shard1;

    @Autowired
    private StringRedisTemplate redis;

    public Map<String, Object> getUser(int id) {

        String cacheKey = "user:" + id;

        // 🔴 CHECK REDIS
        String cached = redis.opsForValue().get(cacheKey);

        if (cached != null) {
            String[] parts = cached.split(":");

            Map<String, Object> res = new HashMap<>();
            res.put("source", "redis");
            res.put("shard", parts[0]);
            res.put("data", parts[1]);
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

        // 🔵 CACHE WITH TTL
        String value = shard + ":" + result;
        redis.opsForValue().set(cacheKey, value, 60, TimeUnit.SECONDS);

        Map<String, Object> res = new HashMap<>();
        res.put("source", "db");
        res.put("shard", shard);
        res.put("data", result);

        return res;
    }
}