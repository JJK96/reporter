module(...,package.seeall)

local tools = {}

function pairsByKeys (t, f)
    local a = {}
    for n in pairs(t) do table.insert(a, n) end
    table.sort(a, f)
    local i = 0      -- iterator variable
    local iter = function ()   -- iterator function
      i = i + 1
      if a[i] == nil then return nil
      else return a[i], t[a[i]]
      end
    end
    return iter
end

function toolslist()
    local output = ""
    for name, tool in pairsByKeys(tools) do
        if tool.references > 0 then
            item = "\\item[" .. name .. "] " .. tool.description 
            if tool.link and not (tool.link == '') then
                item = item .. "\\footnote{\\url{" .. tool.link .. "}}"
            end
            output = output .. item .. "\\toolslabeltext{" .. name .. "}{" .. name .. "}"
        end
    end
    if not (output == "") then
        tex.print("\\toolslistheader")
        tex.print("\\begin{description}")
        tex.print(output)
        tex.print("\\end{description}")
    end
end

function reftool(name)
    if tools[name] == nil then
        tex.print("\\PackageError{tools}{The tool \"" .. name .. "\" is not defined}{The tool should be defined using \\declaretool}")
        return
    end
    tools[name].references = tools[name].references+ 1
end

function declaretool(name, description, link)
    tools[name] = { 
        description = description, 
        link = link,
        references = 0
    }
end
