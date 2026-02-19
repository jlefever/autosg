local Entity = {}
Entity.__index = Entity

function Entity.new(id)
    local self = setmetatable({}, Entity)
    self.id = id
    self.components = {}
    return self
end

function Entity:addComponent(name, data)
    self.components[name] = data
    return self
end

function Entity:getComponent(name)
    return self.components[name]
end

function Entity:hasComponent(name)
    return self.components[name] ~= nil
end

local World = {}
World.__index = World

function World.new()
    local self = setmetatable({}, World)
    self.entities = {}
    self.nextId = 1
    return self
end

function World:createEntity()
    local entity = Entity.new(self.nextId)
    self.nextId = self.nextId + 1
    table.insert(self.entities, entity)
    return entity
end

function World:query(...)
    local required = {...}
    local results = {}
    for _, entity in ipairs(self.entities) do
        local match = true
        for _, comp in ipairs(required) do
            if not entity:hasComponent(comp) then
                match = false
                break
            end
        end
        if match then
            table.insert(results, entity)
        end
    end
    return results
end

local world = World.new()

local player = world:createEntity()
player:addComponent("position", {x = 0, y = 0})
player:addComponent("velocity", {x = 1, y = 0})
player:addComponent("health", {current = 100, max = 100})

local wall = world:createEntity()
wall:addComponent("position", {x = 5, y = 5})
wall:addComponent("solid", {blocking = true})

local movable = world:query("position", "velocity")
for _, entity in ipairs(movable) do
    local pos = entity:getComponent("position")
    local vel = entity:getComponent("velocity")
    pos.x = pos.x + vel.x
    pos.y = pos.y + vel.y
    print(string.format("Entity %d moved to (%d, %d)", entity.id, pos.x, pos.y))
end
